#movies = ["The Holy Grailliam","1975","Terry Jones & Terry Gilliam","91",
#           ["Graham Chapman",["Michael Palin","John Cleese","Terry Gilliam","Eric Idle","Terry Jones"]]]

#print(movies)

"""this is comment!! """

def print_loop(loop_list,indent=False,level=0):
	for loopitem in loop_list:
		if isinstance(loopitem,list):
			print_loop(loopitem,indent,level+1)
		else :
			if indent:
				for tab_stop in range(level):
					print("\t",end='')
			print(loopitem)	

#print_loop(movies)
