import misc
import math

class linearPricing:
	@staticmethod
	def objective(x, params):
		price = params["price"]
		obj = 0
		for x_t,c_t in zip(x, price):
			obj += c_t * x_t
		return obj
	
	@staticmethod
	def restrict_signs(x_min, x_max, params):
		price = params["price"]
		T = len(price)
		for t in range(T):
			if price[t]<0:
				if signs[t]:
					x_min[t] = max(0, x_min[t])
					x_max[t] = max(0, x_max[t])
				else:
					x_min[t] = min(0, x_min[t])
					x_max[t] = max(0, x_max[t])
	
	# Solves BC instances where 0 <= params["price"][t] for all t to optimality. 
	@staticmethod
	def BC_loss_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, eta_c, eta_d, params, eps=1e-6):
		SoC_min = SoC_min[:]
		SoC_max = SoC_max[:]
		price   = params["price"]

		T = len(x_min)
		jobs = [(initialSoC, True, 0, T)]
		x = T*[0]
		for job in jobs:
			SoC0, dummy, t1, t2 = job
			_params = {}
			_params["price"]   = price[t1:t2]
			x[t1:t2] = linearPricing.EVC_loss_opt(SoC0, SoC_max[t2-1], x_min[t1:t2], x_max[t1:t2], eta_c, eta_d, _params, dummy, eps)
			del _params
			if misc.BC_conv_feasible_solution([misc.transform(x_t, 1/eta_c, 1/eta_d) for x_t in x[t1:t2]], SoC0, SoC_min[t1:t2], SoC_max[t1:t2], x_min[t1:t2], x_max[t1:t2], eta_c, eta_d, eps):
				continue
			else:
				if t2 - t1 <= 1:
					# Infeasible instance
					raise ValueError
				max_violation = -math.inf
				k = None
				for i,ps in enumerate(misc.partial_sum(x[t1:t2], SoC0)):
					violation = max(ps - SoC_max[t1+i], SoC_min[t1+i] - ps)
					if violation > max_violation:
						k = t1+i
						max_violation = violation
				if SoC0 + sum(x[t1:k+1]) >= SoC_max[k]:
					v = SoC_min[k] = SoC_max[k]
				else:
					v = SoC_max[k] = SoC_min[k]
				jobs.append((SoC0, False, t1, k+1))
				jobs.append((v,    dummy, k+1, t2))
		return [misc.transform(x_t, 1/eta_c, 1/eta_d) for x_t in x]
		
	# Solves EVC instances where 0 <= params["price"][t] for all t to optimality.
	@staticmethod
	def EVC_loss_opt(initialSoC, targetSoC, x_min, x_max, eta_c, eta_d, params, dummyAtEnd = False, eps=1e-6):
		price = params["price"]
		T = len(x_min)
		A = []
		for t in range(T):
			if x_min[t] <= 0:
				if x_max[t] <= 0:
					A.append((t, price[t]/eta_d, x_max[t]))
				else:
					A.append((t, price[t]/eta_d, 0))
					A.append((t, price[t]/eta_c, x_max[t]))
			else:
				if x_max[t] <= 0:
					A.append((t, price[t]/eta_d, x_max[t]))
				else:
					A.append((t, price[t]/eta_c, x_max[t]))
		fill_level = initialSoC + sum(x_min)
		x = x_min[:]
		for t, multiplier, x_bound in sorted(A, key=lambda x: x[1]):
			if (dummyAtEnd and multiplier >= -eps) or fill_level >= targetSoC - eps:
				break
			if x_bound < x[t]:
				continue
			delta = min(x_bound - x[t], targetSoC - fill_level)
			fill_level += delta
			x[t] += delta
		return x
	
	@staticmethod
	def BC_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps=1e-6):
		SoC_min = SoC_min[:]
		SoC_max = SoC_max[:]
		price = params["price"]
		T = len(x_min)
		jobs = [(initialSoC, True, 0, T)]
		x = T*[0]
		for job in jobs:
			SoC0, dummy, t1, t2 = job
			_params = {}
			_params["price"] = price[t1:t2]
			x[t1:t2] = linearPricing.EVC_opt(SoC0, SoC_max[t2-1], x_min[t1:t2], x_max[t1:t2], _params, dummy, eps)
			del _params
			if misc.BC_feasible_solution(x[t1:t2], SoC0, SoC_min[t1:t2], SoC_max[t1:t2], x_min[t1:t2], x_max[t1:t2], eps):
				continue
			else:
				if t2 - t1 <= 1:
					raise ValueError
				max_violation = -math.inf
				k = None
				for i,ps in enumerate(misc.partial_sum(x[t1:t2], SoC0)):
					violation = max(ps - SoC_max[t1+i], SoC_min[t1+i] - ps)
					if violation > max_violation:
						k = t1+i
						max_violation = violation
				if SoC0 + sum(x[t1:k+1]) > SoC_max[k]:
					v = SoC_min[k] = SoC_max[k]
				else:
					v = SoC_max[k] = SoC_min[k]
				print(t1, k+1)
				print(k+1, t2)
				jobs.append((SoC0, False, t1, k+1))
				jobs.append((v,    dummy, k+1, t2))
		return x

	@staticmethod
	def EVC_opt(initialSoC, targetSoC, x_min, x_max, params, dummyAtEnd = False, eps=1e-6):
		price = params["price"]
		T = len(x_min)
		A = [(t, price[t], x_max[t]) for t in range(T)]
		fill_level = initialSoC + sum(x_min)
		x = []
		for t in range(T):
			x.append(x_min[t])
		for t, multiplier, x_bound in sorted(A, key=lambda x: x[1]):
			if (dummyAtEnd and multiplier >= -eps) or fill_level >= targetSoC - eps:
				break
			delta = min(x_bound - x[t], targetSoC - fill_level)
			fill_level += delta
			x[t] += delta
		return x
	
	@staticmethod
	def signs_from_lossless(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps=1e-6):
		return [x_t > 0 for x_t in linearPricing.BC_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps)]
