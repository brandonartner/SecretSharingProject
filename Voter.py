from fractions import Fraction
from Crypto.PublicKey import DSA
from Crypto.Util import number
from Crypto.Random import random
from sympy.abc import x
from Toolkit import *

import sympy

class Voter:
	"""	Voter implements a (n,k)-threshold scheme which is capable of submiting 
		a signature.
	"""

	def __init__(self, node, n, k, prime_size=1024):
		'''	
			n: total number of keys for the voter
			k: the required number of votes
			prime_size: number of bits for the prime number, default:1024
							Must be a multiple of 64
		'''
		self.prime_size = prime_size
		self.p = number.getStrongPrime(prime_size,false_positive_prob=1e-10)
		self.n = n
		self.k = k
		self.values = [[], []]
		self.pubKey = None
		self.node = node

	def generate_scheme(self, data=None):
		'''	Generates the private-public key pair, the polynomial, and the keys
			for this voter.

			data: If the voter is not the root voter then there should be a piece of data passed in...
		'''
		if not data:
			print('Creating new DSA pair.')
			# Generate the DSA public-private key pair for signing with
			key = DSA.generate(self.prime_size)
			# Set the prime equal to the modulus from the DSA key set
			self.p = key.p
			# Set the public key to the public key from the DSA key set
			self.pubKey = key.y
			data = key.x
		'''
		else:
			print('Creating new DSA pair.')
			# Generate the DSA public-private key pair for signing with
			key = DSA.importKey(convert_to_format(data))
			# Set the prime equal to the modulus from the DSA key set
			self.p = key.p
			# Set the public key to the public key from the DSA key set
			self.pubKey = key.y
			data = key.x
		'''

		# Generate a polynomial
		poly = self.generate_polynomial(data%self.p)
		# Reutrn a set of keys generated from the polynomial
		return self.generate_keys(poly)

	def random_distinct(self, lo, hi, size):
		''' Used to get lists of distinct random numbers,

		    lo: Low bound for searching
		    hi: High bound for searching
		    
		    Returns: Random numbers within bounds
		'''

		v = []

		while len(v) < size:
			rand = random.randint(lo, hi)
		    
			if rand not in v:
				v.append(rand)
		        
		return v

	def generate_polynomial(self, data):
		''' Makes a random polynomial with data as the coeficient term.
			
			data: The data as a numeric value to be split
			
			Returns: polynomial as a string and as a lambda function
		'''

		# Shamir's algorithms requires each coefficient to be distinct
		#coefficients = random.sample((x for x in range(self.p)), self.k-1) 
		coefficients =  self.random_distinct(0, self.p, self.k-1)

		# start building our polynomial
		polynomial = ''
		power = self.k-1

		while power > 0:
			# each a_i*x^i for i from k-1 to 1
			polynomial = polynomial + '{}*x**{}+'.format(coefficients[-power], power)
			power -= 1

		# set a_0 to data
		polynomial = polynomial + '{}'.format(data)

		# convert polynomial string to lambda function
		f = sympy.utilities.lambdify(x, sympy.sympify(polynomial))

		return f

	def generate_keys(self, poly):
		''' Creates the keys

			poly: Polynomial function to create the keys

			Returns: n-tuple of keys
		'''

		# create distinct x values because f(a)=f(b) iff a=b 
		# implies less than n keys will be made
		#X = random_distinct(1, p, n)
		X = range(1, self.n+1)

		# get corresponding y values
		Y = [poly(x) % self.p for x in X]

		return list(zip(X, Y))


	def add_key_to_signature(self, key, doc):
		''' 
			Adds given key and feeds forward.

			Returns: soln - when k keys have been submitted, the original data
							otherwise, None
		'''

		# splitting the key across first two lists
		self.values[0].append(key[0])
		self.values[1].append(key[1])

		
		# generate the as far forward as possible in the Neville list
		# ie. if 3 keys have been submitted, 3 entries in the list can be made
		for idx, lst in enumerate(self.values[1:]):
			# for every sublist that has 2 elements, generate the corresponding  LIP
		    if len(lst) == 2:
		        val = self.firstOrderLag(idx)
		        
		        if idx == len(self.values)-2:
		            self.values.append([self.find_divisible_congruency(val)])
		        else:
		            self.values[idx+2].append(self.find_divisible_congruency(val))
		            
				# remove now unnecessary value from current sublist
		        self.values[idx+1].pop(0)

		# if there are k elements, than we are done, delete all elements and return the last value
		if len(self.values[0]) == self.k:
		    self.sign(self.values[-1][0], doc)
		    for i in range(len(self.values)):
		        self.values[i] = []


	def firstOrderLag(self, idx):
		''' Calculates the nth-ordered Lagrangian Interpolating Polynomial, evaluated at 0.
		'''
		j = -1
		i = j - (idx + 1)

		x1 = self.values[0][i]
		x2 = self.values[0][j]

		y1 = self.values[idx+1][-2]
		y2 = self.values[idx+1][-1]

		num = (0-x2)*y1-(0-x1)*y2
		den = x1-x2
		return Fraction(num, den)


	def find_divisible_congruency(self, fraction):
		''' Calculates a congruent integer to the numerator that is divisible by the denominator.
			Input: fraction, the fraction in question.
			Return: The z such that z = (num + i*prime)/den and z is an integer (without trunction).
		'''
		# Fracction class is used here because float division can't handle crypto-secure sized numbers,
		#  but Fraction uses integers, which can handle effectively infinite numbers
		num = Fraction(fraction.numerator % self.p,1)
		den = Fraction(fraction.denominator % self.p,1)

		i = 0
		z = (self.p*i+num)/den

		while z != int(z):
			i += 1
			z = (self.p*i+num)/den

		return int(z)

	def sign(self, private_key, doc):
		'''
			Function creates the digital signature for the scheme.
			doc: Data that is being signed
			Return: Digital Signature
		'''
		# Sign the document. 
		# If voter is a subvoter, also send key to parent.
		#
		print(data_to_key(private_key,self.n))
		print(doc)
		
		if self.node.parent:
			self.node.vote(doc, key=data_to_key(private_key,self.n))
		