class bankacount:
    def __init__(self,name,id,balance,loc):
        self.name = name
        self.id = id
        self.balance = balance
        self.loc = loc

    def deposit(self,amount):
        self.balance+= amount
    def withdraw(self,amount):
        if(self.balance< amount):
                print("is not engouh")
                pass
        self.balance-=amount
    def transfer(self,target,amount):
        if(self.balance< amount):
            print("is not engouh")
            pass
        self.balance-= amount
        target.balance+= amount
    def getbalance(self):
        print(self.balance)

    def __str__(self):
        return str(self.name), str(self.balance)

Kerwin = bankacount("Kerwin",1,10000,"Shanghai")
Kerwin.getbalance()