list1 = [4,5,1,2,3]
list2 = ['a','t','c','p','s']


print [list(x) for x in zip(*sorted(zip(list1, list2), key=lambda pair: pair[0]))]