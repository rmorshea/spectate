from spectate import mvc


d = mvc.Dict()
l = mvc.List()
s = mvc.Set()


@mvc.view(d)
@mvc.view(l)
@mvc.view(s)
def printer(event):
    print(event)


d['a'] = 1
l.append(2)
s.add(3)
