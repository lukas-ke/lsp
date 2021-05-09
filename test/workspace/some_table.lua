local InnerTable = {
  a=1
}

local SomeTable = {
  x=1,
  y=2,
  z="Hello",
  other=InnerTable,
  misc=Flypp
}

GlobalTable = {}

return SomeTable
