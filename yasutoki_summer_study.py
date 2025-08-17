# def tashi(a,b):
#     x = a + b
#     return x

# z = tashi(3,2)
# print(z)

import time

def keisan(a,b,t):
    if t == "たし":
        x = a + b
    elif t == "ひき":
        x = a - b
    elif t == "かけ":
        x = a * b
    elif t == "わり":
        x = a / b
    else:
        x = "エラー"
    
    return x

# c = keisan(3,1,"かけ")
# print(c)

# a = keisan(2,3,"かけ")
# print(a)

for i in range(20):
    c = keisan(i,i+1,"たし")
    print(i,"回目 ", c)
    time.sleep(1)

i = 0
end_flg = False
while end_flg == False:
    c = keisan(i,i+1,"たし")
    print(i,"回目 ", c)
    i = i + 1

    if i > 30:
        end_flg = True


# class Keisan():
#     def add(self,a,b): 
#         return (a + b)
#     def sub(self,a,b):
#         return (a - b)
#     def times(self,a,b):
#         return (a * b)
#     def div(self,a,b):
#         return (a / b)

# keisan = Keisan()

# ans = keisan.add(3,4)
# print(ans)




