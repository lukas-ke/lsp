my_table = {
  x = 42,
  xavier="Professor",
  y = 100
}

my_text = "korv"

global_value = 100

function a_function(a,b)
  return a
end

function other_function(x, y, z)
  return x
end

my_table.print_x = function(self)
  -- print(tostring(self.x)) TODO: Fix call parsing
end

t1 = {
  t2 = {
    t3 = {
      value=1000,
      f=function(x,y) end
    }
  }
}
