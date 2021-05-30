local function test_local()
 local x = 3
 if true then
  local x = 5
 end
 assert(x == 3)
end

local function test_inner_local()

 if true then
  local x = 5
 end
 assert(x == nil)
end

local function test_redundant_local()
 local x = 5
 local x = 7
 assert(x == 7)
end

test_local()
test_inner_local()
test_redundant_local()
