;;; -*- coding: utf-8; lexical-binding: t -*-

(require 'lsp-mode)
(require 'lua-mode)

;; Make the path to this file (luk-lsp.el) available as
;; `luk-lsp-path' when this file is loaded
;; Note: This won't happen on plain eval.
(if load-file-name
    (setq luk-lsp-path (file-name-directory load-file-name))
  (if buffer-file-name
      (setq luk-lsp-path (file-name-directory (buffer-file-name)))
    (error "Neither load-file-name nor buffer-file-name")))

(defun luk-lsp-default-server-path ()
  "Use a path relative to this file as the default for finding run_lua_server.py"
  (concat
   (file-name-as-directory (parent-dir (parent-dir luk-lsp-path)))
   "run_lua_server.py"))

(defgroup luk-lsp-lua nil
  "LSP support for my hack lua language server."
  :group 'lsp-mode)

(defcustom luk-lsp-lua-server-path
  (luk-lsp-default-server-path)
  "Path to lua_server.py"
  :type 'string
  :group 'luk-lsp-lua)

(defcustom luk-lsp-lua-python-command
  "python"
  "Command for running Python"
  :type 'string
  :group 'luk-lsp-lua)

(defcustom luk-lsp-lua-server-options
  nil
  "Command line options for the server"
  :type '(repeat (string))
  :group 'luk-lsp-lua)

(defun luk-lsp-lua--create-connection ()
  "Create connection to my lua language server."
  (lsp-stdio-connection
   (lambda ()
     (append (list luk-lsp-lua-python-command luk-lsp-lua-server-path) luk-lsp-lua-server-options))
   (lambda ()
     (f-exists? luk-lsp-lua-server-path))))

(lsp-register-client
 (make-lsp-client :new-connection (luk-lsp-lua--create-connection)
                  :major-modes '(lua-mode)
                  :priority 1
                  :server-id 'luk-server))

(defun luk-lsp-setup-keys()
  (interactive)
  (define-key lua-mode-map (kbd "M-,") 'company-complete)
  (define-key lua-mode-map (kbd "C-c g") 'lsp-find-definition))

(defun luk-lsp-setup-all()
  (luk-lsp-setup-keys)

  ;; So that it restarts if I kill all buffers
  ;; (Maybe there's some manual way to do it?)
  (setq lsp-keep-workspace-alive nil))

(provide 'luk-lsp)
