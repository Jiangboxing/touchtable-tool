def partial_sum(xs, start=0):
    sum = start
    for x in xs:
        sum += x
        yield sum

def transform(x, eta_c, eta_d):
    return (eta_c if x >= 0 else eta_d) * x
        
def BC_feasible_solution(x, initialSoC, SoC_min, SoC_max, x_min, x_max, eps=1e-6):
	if x == [] and SoC_min == [] and SoC_max == [] and x_min == [] and x_max == []:
		return True
	SoCt = initialSoC
	for t in range(len(x)):
		if x[t] < x_min[t] - eps or x[t] > x_max[t] + eps:
			return False
		SoCt += x[t]
		if SoC_min[t] - eps > SoCt or SoCt > SoC_max[t] + eps:
			return False
	return True

def BC_conv_feasible_solution(x, initialSoC, SoC_min, SoC_max, x_min, x_max, eta_c, eta_d, eps=1e-6):
	SoCt = initialSoC
	for t in range(len(x)):
		if (eta_c if x[t] > 0 else eta_d) * x[t] < x_min[t] - eps or (eta_c if x[t] > 0 else eta_d) * x[t] > x_max[t] + eps:
			return False
		SoCt += (eta_c if x[t] > 0 else eta_d) * x[t]
		if SoC_min[t] - eps > SoCt or SoCt > SoC_max[t] + eps:
			return False
	return True