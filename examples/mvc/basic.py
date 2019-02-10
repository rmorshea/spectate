from spectate import mvc


my_dict = mvc.Dict()
my_list = mvc.List()
my_set = mvc.Set()


@mvc.view(my_dict)
@mvc.view(my_list)
@mvc.view(my_set)
def printer(event):
    print(event)


my_dict["a"] = 1
my_list.append(2)
my_set.add(3)
