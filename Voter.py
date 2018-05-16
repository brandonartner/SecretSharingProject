from fractions import Fraction
from Crypto.PublicKey import DSA
from Crypto.Util import number
from Crypto.Random import random
from sympy.abc import x
from Toolkit import *
import hashlib

import sympy

class Voter:
	"""	Voter implements a (n,k)-threshold scheme which is capable of submiting 
		a signature.

    Attributes:
        prime_size (int): Size of the prime number. (Default: 1024)
        p (int): The prime number.
        n (int): The number of keys to make with Shamir's Scheme.
        k (int): The number of keys required to construct the data.
        values (list): The values for the active Asynchronous Neville's Method.
        pubKey (PubKey): Public Key object for DSA.
        node (TreeNoe): The node this Voter belongs to.

    Note:
    	Digital Signature Specifications (DSS) specifies that the prime length should be 1024/2048 (Can't Remember).

	"""

	def __init__(self, node, n, k, prime_size=1024):
		"""Initializes a Voter object.

		Args:
	        node (TreeNode): A reference back to the node this voter belongs to.

	        n (int): The number of key to generate for this voter.

	        k (int): The number of vote required to pass a vote.

	        prime_size (int): The number of bits for the prime number.
	    						default: 1024
	    						Must be a multiple of 128 between 512 and 1024.

        """

		self.prime_size = prime_size
		self.p = number.getStrongPrime(prime_size,false_positive_prob=1e-10)
		self.n = n
		self.k = k
		self.values = [[], []]
		self.pubKey = None
		self.node = node

	def generate_scheme(self, data=None):
		"""Generates the private-public key pair, the polynomial, and the keys for this voter.

        Args:
	        data (int): The data to be used as the secret data. 
	    						(Note: None means the voter is for root node.)
	        
	    Returns: 
	    	list of int tuples: list of key pairs generated by Shamir's Scheme.

        Todo: 
        	Implement non-root DSA key pairs. This is to allow for signing of sub-root
        	document sets. Problem consists of being given a private key and having to 
        	generate a public key.

        """

		if not data:
			print('Creating new DSA pair.')
			# Generate the DSA public-private key pair for signing with
			key = DSA.generate(self.prime_size)
			# Set the prime equal to the modulus from the DSA key set
			self.pubKey = key.publickey()
			self.p = self.pubKey.p
			# Set the public key to the public key from the DSA key set
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
		poly = generate_polynomial(data%self.p, self.k, self.p)
		# Reutrn a set of keys generated from the polynomial
		return generate_keys(poly, self.n, self.p)


	def add_key_to_signature(self, key, doc):
		"""Function implements the Asynchronous Neville's Method and adds the given key to the in progress vote. 

        Args:
	        key (int, int): The key being added to the LIP.

	        doc (String, String): The document being voted on.

	    Returns: 
	    	(int,int): DSA Signature. if the vote is completed, i.e. k keys have been submitted.
	        boolean: VoteIsSuccessful. True if vote was finished.

        Todo:
        	Ensure that the submitted key is actually valid. ie. It is from the set of keys originally generated
        	for this voter.

    	Note:
    		This function returns both a signature if there is one, and a boolean of whether
    		or not a vote has finished.

        """

		# splitting the key across first two lists
		self.values[0].append(key[0])
		self.values[1].append(key[1])

		
		# generate the as far forward as possible in the Neville list
		# ie. if 3 keys have been submitted, 3 entries in the list can be made
		for idx, lst in enumerate(self.values[1:]):
			# for every sublist that has 2 elements, generate the corresponding  LIP
		    if len(lst) == 2:
		        val = nthOrderLag(self.values, idx)
		        
		        if idx == len(self.values)-2:
		            self.values.append([find_divisible_congruency(val, self.p)])
		        else:
		            self.values[idx+2].append(find_divisible_congruency(val, self.p))
		            
				# remove now unnecessary value from current sublist
		        self.values[idx+1].pop(0)

		# if there are k elements, than we are done, delete all elements and return the last value
		if len(self.values[0]) == self.k:
			signature = self.sign(doc, self.values[-1][0])
			for i in range(len(self.values)):
				self.values[i] = []
			return signature, True

		return None, False

	def sign(self, doc, private_key):
		"""Function creates the digital signature for a given document with this voter's private key.

        Args:
        	doc (String, String): The document that is being signed.

            private_key (int): The private key for the DSA pair. (Comes from add_key_to_signature)

        Returns: 
        	(int, int): A signature if this node has a public key, else None.

        Todo: 
        	Right now the doc param is a string 2-tuple, this might be better as just a String since all 
    		that is needed is the document text and it would be more intuitive for future users.
        """

		if self.node.parent:
			# If voter is a subvoter, also send key to parent.
			self.node.vote(doc, key=data_to_key(private_key,self.n))

		if self.pubKey:
			# Sign the document. 
			key = DSA.construct((self.pubKey.y, self.pubKey.g, self.pubKey.p, self.pubKey.q, private_key))

			m = hashlib.sha256()
			m.update(doc[1].encode())
			h = m.digest()
			k = random.StrongRandom().randint(1,key.q-1)

			signature = key.sign(h,k)

			return signature

		return None

		
	def verify(self,doc, signature):
		"""Function verifies a digital signature. for a given document with this voter's public key.

        Args:
        	doc (String): The document that is being signed.

        	signature (int, int): DSA signature being verified.

        Returns: 
        	boolean: True if the voter has a public key and the signature is correct, False otherwise.

        """

		if self.pubKey:
			m = hashlib.sha256()
			m.update(doc.encode())
			h = m.digest()

			return self.pubKey.verify(h,signature)

		return False