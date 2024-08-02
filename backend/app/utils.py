def cycle_list(list_to_cycle, round=3):
	div = len(list_to_cycle) % round
	if div != 0:
		if len(list_to_cycle) > round:
			return list_to_cycle + list_to_cycle[0:round - div]
	return list_to_cycle