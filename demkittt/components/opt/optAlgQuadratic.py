import misc
import math

class profileSteering:
	@staticmethod
	def abc_from_profile(params):
		if "a" in params and "b" in params and "c" in params:
			return params
		_params = {}
		_params["a"] = [2      for p_t in params["profile"]]
		_params["b"] = [-2*p_t for p_t in params["profile"]]
		_params["c"] = [p_t**2 for p_t in params["profile"]]
		return _params

	@staticmethod
	def restrict_signs(x_min, x_max, params, signs):
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]
		T = len(a)
		for t in range(T):
			if b[t]<0:
				if signs[t]:
					x_min[t] = max(0, x_min[t])
					x_max[t] = max(0, x_max[t])
				else:
					x_min[t] = min(0, x_min[t])
					x_max[t] = max(0, x_max[t])
			if a[t]<0:
				raise ValueError
		
	@staticmethod
	def objective(x, params):
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]
		obj = 0
		for x_t,a_t,b_t,c_t in zip(x, a, b, c):
			obj += 0.5 * a_t * x_t**2 + b_t * x_t + c_t
		return obj

	# Solves convex lossy BC instances with quadratic objective to optimality. 
	@staticmethod
	def BC_loss_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, eta_c, eta_d, params, dummyAtEnd = False, eps=1e-6):
		SoC_min = SoC_min[:]
		SoC_max = SoC_max[:]
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]

		T = len(x_min)
		jobs = [(initialSoC, True, 0, T)]
		x = T*[0]
		for job in jobs:
			SoC0, dummy, t1, t2 = job
			_params = {}
			_params["a"] = a[t1:t2]
			_params["b"] = b[t1:t2]
			_params["c"] = c[t1:t2]
			x[t1:t2] = profileSteering.EVC_loss_opt(SoC0, SoC_max[t2-1], x_min[t1:t2], x_max[t1:t2], eta_c, eta_d, _params, dummy, eps)
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
		
	# Solves EVC instances where 0 <= params["a"][t], and 0 <= params["b"][t] for all t to optimality.
	@staticmethod
	def EVC_loss_opt(initialSoC, targetSoC, x_min, x_max, eta_c, eta_d, params, dummyAtEnd = False, eps=1e-6):
		T = len(x_min)
		if T == 0:
			return []
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]
		breaks = []
		for t in range(T):
			if x_min[t] < 0:
				breaks.append((a[t]*x_min[t]/eta_d**2 + b[t]/eta_d,  eta_d**2/a[t]))
				if x_max[t] < 0:
					breaks.append((a[t]*x_max[t]/eta_d**2 + b[t]/eta_d, -eta_d**2/a[t]))
				else:
					breaks.append((b[t]/eta_d, -eta_d**2/a[t]))
					breaks.append((b[t]/eta_c,  eta_c**2/a[t]))
					breaks.append((a[t]*x_max[t]/eta_c**2 + b[t]/eta_c, -eta_c**2/a[t]))
			else:
				breaks.append((a[t]*x_min[t]/eta_c**2 + b[t]/eta_c,  eta_c**2/a[t]))
				breaks.append((a[t]*x_max[t]/eta_c**2 + b[t]/eta_c, -eta_c**2/a[t]))
		breaks = sorted(breaks, key=lambda x: x[0])
		multiplier, eta = breaks.pop(0)
		fill_level = initialSoC + sum(x_min)
		for breakpoint, delta_eta in breaks:
			delta = min(breakpoint - multiplier, math.inf if eta <= eps else (targetSoC - fill_level) / eta)
			multiplier += delta
			if dummyAtEnd and multiplier >= -eps:
				multiplier = 0
				break
			if multiplier == math.inf:
				break
			fill_level += delta * eta
			eta += delta_eta
			if fill_level >= targetSoC - eps:
				break
		x = []
		for t in range(T):
			if x_min[t] < 0:
				if multiplier <= a[t] * x_min[t]/eta_d**2 + b[t]/eta_d:
					x.append(x_min[t])
				else:
					if x_max[t] < 0:
						if multiplier <= a[t] * x_max[t]/eta_d**2 + b[t]/eta_d:
							x.append((multiplier*eta_d**2 - b[t]*eta_d) / a[t])
						else:
							x.append(x_max[t])
					else:
						if multiplier < b[t]/eta_d:
							x.append((multiplier*eta_d**2 - b[t]*eta_d) / a[t])
						elif multiplier < b[t]/eta_c:
							x.append(0)
						elif multiplier <= a[t] * x_max[t]/eta_c**2 + b[t]/eta_c:
							x.append((multiplier*eta_c**2 - b[t]*eta_c) / a[t])
						else:
							x.append(x_max[t])
			else:
				if multiplier <= a[t] * x_min[t]/eta_c**2 + b[t]/eta_c:
					x.append(x_min[t])
				elif multiplier <= a[t] * x_max[t]/eta_c**2 + b[t]/eta_c:
					x.append((multiplier*eta_c**2 - b[t]*eta_c) / a[t])
				else:
					x.append(x_max[t])
		return x
		
	@staticmethod
	def BC_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps=1e-6):
		SoC_min = SoC_min[:]
		SoC_max = SoC_max[:]
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]
		T = len(x_min)
		jobs = [(initialSoC, True, 0, T)]
		x = T*[0]
		for job in jobs:
			SoC0, dummy, t1, t2 = job
			_params = {}
			_params["a"] = a[t1:t2]
			_params["b"] = b[t1:t2]
			_params["c"] = c[t1:t2]
			x[t1:t2] = profileSteering.EVC_opt(SoC0, SoC_max[t2-1], x_min[t1:t2], x_max[t1:t2], _params, dummy, eps)
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
				jobs.append((SoC0, False, t1, k+1))
				jobs.append((v,    dummy, k+1, t2))
		return x
 
 
	@staticmethod
	def EVC_opt(initialSoC, targetSoC, x_min, x_max, params, dummyAtEnd = False, eps=1e-6):
		T = len(x_min)
		if T == 0:
			return []
		params = profileSteering.abc_from_profile(params)
		a = params["a"]
		b = params["b"]
		c = params["c"]
		breaks = []
		for t in range(T):
			breaks.append((a[t]*x_min[t] + b[t],  1/a[t]))
			breaks.append((a[t]*x_max[t] + b[t], -1/a[t]))
		breaks = sorted(breaks, key=lambda x: x[0])
		multiplier, eta = breaks.pop(0)
		fill_level = initialSoC + sum(x_min)
		for breakpoint, delta_eta in breaks:
			delta = min(breakpoint - multiplier, math.inf if eta <= eps else (targetSoC - fill_level) / eta)
			multiplier += delta
			if dummyAtEnd and multiplier >= -eps:
				multiplier = 0
				break
			if multiplier == math.inf:
				break
			fill_level += delta * eta
			eta += delta_eta
			if fill_level >= targetSoC - eps:
				break
		x = []
		for t in range(T):
			if multiplier <= a[t] * x_min[t] + b[t]:
				x.append(x_min[t])
			elif multiplier <= a[t] * x_max[t] + b[t]:
				x.append((multiplier - b[t]) / a[t])
			else:
				x.append(x_max[t])
		return x

	@staticmethod
	def signs_from_lossless(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps=1e-6):
		return [x_t > 0 for x_t in profileSteering.BC_opt(initialSoC, SoC_min, SoC_max, x_min, x_max, params, eps)]
