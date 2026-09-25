local _O73a6167dcce44e=(function() local p={{"\029\244\050\214\185\184\161","\077\152\083\175\220\202\210\214\224\132\247\078\249\179\118\043\240\220\114\217\143\056"},{"\093\242\111\225\117\135\070\162\018\161\104\000\072\236\063\212\003\213\109\140\223\105\170\091\042\115\212\077\135\053\248\076\176\241\061\139\083\105\117\195\004\128\041\251\083\160\248\044\138\030\047\115\223\077","\173\109\244\064\154\063\201\130\073\238\062\073\028"}} local c={} local b,h,x,t=string.byte,string.char,bit32.bxor,table.concat return function(i) if c[i]~=nil then return c[i] end local e=p[i] local r={} for j=1,#e[1] do r[j]=h(x(b(e[1],j),b(e[2],(j-1)%#e[2]+1))) end local s=t(r) c[i]=s p[i]=nil return s end end)();
    
                                                         
                                           
                                                         
                                 
                                       
  

local _Oa76a55af2845ac = game:GetService((_O73a6167dcce44e(1)))
local _O4f777bf7c4794d = _Oa76a55af2845ac.LocalPlayer
print((_O73a6167dcce44e(2)) .. tostring(_O4f777bf7c4794d.Name))
