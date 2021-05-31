from lsp.util import make_response
from lsp.lsp_defs import (
    CompletionParams,
    DefinitionParams,
    DidCloseTextDocumentParams,
    InitializeResult,
    NotificationMessage,
    Position,
    SignatureHelpParams,
    TextDocumentContentChangeEvent,
    TextDocumentIdentifier,
    TextDocumentPositionParams,
)
from . doc import Document


class LSP_state:
    def __init__(self, db, log):
        self.log = log.prefixed("[LSP_State] ")
        self.initialized = False
        self.shutdown = False
        self.exit = False
        self.db = db
        self.didOpen = {}

    def method(self, content):
        if content["method"] == "initialize":
            self.log.info("Request: initialize")
            return self._initialize(content)

        elif content["method"] == "initialized":
            self.log.info("Notification: initialized")
            return self._initialized(content)

        elif content["method"] == "textDocument/didOpen":
            self.log.info("Notification: textDocument/didOpen")
            return self._textDocument_didOpen(content)

        elif content["method"] == "textDocument/didClose":
            return self._textDocument_didClose(content)

        elif content["method"] == "textDocument/didChange":
            self.log.info("Notification: textDocument/didChange")
            return self._textDocument_didChange(content)

        elif content["method"] == "textDocument/completion":
            self.log.info("Request: textDocument/completion")
            return self._textDocument_completion(content)

        elif content["method"] == "textDocument/definition":
            # The go to definition request is sent from the client to
            # the server to resolve the definition location of a
            # symbol at a given text document position.
            self.log.info("Request: textDocument/definition")
            return self._textDocument_definition(content)

        elif content["method"] == "textDocument/typeDefinition":
            self.log.info("Request: textDocument/typeDefinition")
            return self._textDocument_typeDefinition(content)

        elif content["method"] == "textDocument/signatureHelp":
            return self._textDocument_signatureHelp(content)

        elif content["method"] == "textDocument/hover":
            return self._textDocument_hover(content)

        elif content["method"] == "shutdown":
            self.log.info("Request: shutdown")
            return self._shutdown(content)

        elif content["method"] == "textDocument/documentLink":
            return self._textDocument_documentLink(content)

        elif content["method"] == "exit":
            self.log.info("Notification: exit")
            return self._exit(content)

        else:
            # TODO: Use presence of id to determine if notification or request
            self.log.info(f'unknown request/notification: {content["method"]}')

    def _initialize(self, content):
        self.log.info("Initializing")

        # TODO: Before initialize:
        # .. Notifications should be dropped, except for the exit
        # .. notification. This will allow the exit of a server without
        # .. an initialize request.
        # TODO: Move capabilities to lua_db etc.

        capabilities = self.db.get_capabilities()
        return make_response(content["id"], InitializeResult(
            capabilities=capabilities,
            serverInfo={
                "name": "lsp_io_server",
                "version": "1.0"}))

    def _shutdown(self, content):
        self.log.info("Shutting down")
        self.shutdown = True
        return make_response(content["id"], None)

    def _initialized(self, content):
        self.log.info("initialized notification")
        return None

    def _exit(self, content):
        self.log.info("Exiting")
        if not self.shutdown:
            self.log.error("Client error: Exit without shutdown request")
        self.exit = True
        return None

    def _textDocument_completion(self, content):
        self.log.info(str(content))
        p = CompletionParams.fromDict(content["params"])

        id_ = content["id"]
        completions = []
        if p.textDocument.uri in self.didOpen:  # TODO: Shouldn't be required
            doc = self.didOpen[p.textDocument.uri]
            try:
                completions = self.db.completions(doc, p.position)
            except IndexError as e:
                self.log.error(f"Completion failed with IndexError: {e}")
                completions = []

        return make_response(id_, completions)

    def _textDocument_definition(self, content):
        # Note: called via lsp-find-definition
        self.log.info(content)

        p = DefinitionParams.fromDict(content["params"])
        if p.textDocument.uri in self.didOpen:  # TODO: Shouldn't be required
            doc = self.didOpen[p.textDocument.uri]
            try:
                location = self.db.definition(doc, p.position)
            except IndexError:
                # TODO: Return what
                return make_response(content["id"], None)

        return make_response(content["id"], location)

    def _textDocument_typeDefinition(self, content):
        self.log.info(content)
        params = content["params"]
        textDocument = TextDocumentIdentifier.fromDict(params["textDocument"])
        position = Position.fromDict(params["position"])
        id_ = content["id"]

        # TODO: Should work also for unopened docs
        doc = self.didOpen[textDocument.uri]
        location = self.db.typeDefinition(doc, position)
        return make_response(id_, location)

    def _textDocument_didOpen(self, content):
        # TODO:
        # The document open notification is sent from the client to
        # the server to signal newly opened text documents. The
        # document’s content is now managed by the client and the
        # server must not try to read the document’s content using the
        # document’s Uri. Open in this sense means it is managed by
        # the client. It doesn’t necessarily mean that its content is
        # presented in an editor. An open notification must not be
        # sent more than once without a corresponding close
        # notification send before. This means open and close
        # notification must be balanced and the max open count for a
        # particular textDocument is one. Note that a server’s ability
        # to fulfill requests is independent of whether a text
        # document is open or closed.
        uri = content["params"]["textDocument"]["uri"]
        self.log.info(f"textDocument/didOpen: {uri}")
        text = content["params"]["textDocument"]["text"]
        doc = Document(uri, text, self.log)
        self.didOpen[uri] = doc
        self.db.didOpen(doc)

        # TODO: Only if client has
        # PublishDiagnosticsClientCapabilities
        msg_diag = self._get_diagnostics_notification(doc)
        return msg_diag.toDict()

    def _textDocument_didClose(self, content):
        p = DidCloseTextDocumentParams.fromDict(content["params"])
        uri = p.textDocument.uri
        if uri in self.didOpen:
            del self.didOpen[uri]
            self.log.info(f"Closed: {uri}")
        else:
            # TODO: "A close notification requires a previous open
            # notification to be sent.", client error I guess.
            self.log.info(f"didClose unknown: {uri}")

    def _textDocument_didChange(self, content):
        params = content["params"]
        td = params["textDocument"]
        uri = td["uri"]

        doc = self.didOpen.get(uri)
        if doc is None:
            self.log.error("Error: didOpen for missing document?")
            return

        version = td["version"]
        contentChanges = params["contentChanges"]
        CE = TextDocumentContentChangeEvent
        changes = [CE.fromDict(d) for d in contentChanges]
        doc.contentChanges(changes, version)
        self.db.didChange(doc)

        # TODO: Only if client has
        # PublishDiagnosticsClientCapabilities
        msg_diag = self._get_diagnostics_notification(doc)
        return msg_diag.toDict()

    def _textDocument_signatureHelp(self, content):
        p = SignatureHelpParams.fromDict(content["params"])
        doc = self.didOpen[p.textDocument.uri]
        signatureHelp = self.db.signatureHelp(doc, p.position)
        return make_response(content["id"], signatureHelp)

    def _textDocument_hover(self, content):
        p = TextDocumentPositionParams.fromDict(content["params"])
        hover = self.db.hover(self.didOpen[p.textDocument.uri], p)
        return make_response(content["id"], hover)

    def _textDocument_documentLink(self, content):
        return make_response(content["id"], [])

    def _get_diagnostics_notification(self, doc) -> NotificationMessage:
        # TODO: Only if client has
        # PublishDiagnosticsClientCapabilities
        diagnostics = self.db.get_PublishDiagnosticsParams(doc)
        return NotificationMessage(
            "textDocument/publishDiagnostics",
            diagnostics)
