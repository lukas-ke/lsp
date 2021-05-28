local t = {
  --@return integer
  f1=function(x, y) return 1 end
}
local function f() end
t.f1()
f()
local x = t.f1()
y = t.f1()
