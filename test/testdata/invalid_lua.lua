local function f1()
end

local function f2()
end

f1(), f2()  -- Can't stack functions

f1() = f2() -- Can't assign to function results
