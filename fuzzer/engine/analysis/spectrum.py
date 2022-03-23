import numpy as np
import time
import copy

class Spectrum:
    def __init__(self, nr_jumpis, nr_pcs, granularity="jumpis"):
        self.granularity = granularity

        if granularity == "pcs":
            self.nr_components = nr_pcs
        elif granularity == "jumpis":
            self.nr_components = nr_jumpis
        else: #default
            self.nr_components = nr_pcs
            self.granularity == "pcs"

        if self.nr_components == 0:
            self.nr_components = 1
            #raise ValueError('Number of components in Spectrum must be greater than 0')

        self.transactions = []

        # Used only if ddu_fit_indv flag is enabled
        self.transactions_next_gen = []
        
        # Maps individual hash id to ddu score; resets every generation
        self.gen_indvs_ddu_scores = {}

        self.density = NormalizedRho(self.nr_components)
        self.diversity = GiniSimpson()
        self.uniqueness = Ambiguity(self.nr_components)
        
        self.de = 0
        self.di = 0
        self.u = 0

        self._updated = False
    
    # Attribute individual with ddu value
    def update_indv_ddu(self, indv):
        density, diversity, uniqueness = self.calculate_ddu()
        ddu = density * diversity * uniqueness
        self.gen_indvs_ddu_scores[indv] = ddu
    
    # Remove latest transaction
    def revoke_transaction(self, transaction):
        popped_transaction = self.transactions.pop()
        self.transactions_next_gen.append(popped_transaction)
        #print("REVOKED indiv ", popped_transaction.hash_code)

        self.density.revoke_transaction(transaction)
        self.diversity.revoke_transaction(transaction)
        self.uniqueness.revoke_transaction(transaction)

        self.set_updated_flag(value = True)

    # Include previously revoked transactions
    def update_next_gen_transactions(self):
        for t in self.transactions_next_gen:
            self.update_transactions(t)

        self.transactions_next_gen = []
    

    def update_transactions(self, transaction):
        self.transactions.append(transaction)
        
        self.density.update_transactions(transaction)
        self.diversity.update_transactions(transaction)
        self.uniqueness.update_transactions(transaction)

        self.set_updated_flag(value = True)

    def calculate_ddu(self):
        if not self._updated:
            return self.de, self.di, self.u

        self.de = self.density.calculate_density(len(self.transactions))
        self.di = self.diversity.calculate_diversity()
        self.u = self.uniqueness.calculate_uniqueness(len(self.transactions))

        self.set_updated_flag(value = False)

        return self.de, self.di, self.u

    def set_updated_flag(self, value = True):
        if self._updated != value:
            self._updated = value

    def reset_transactions(self):
        self.transactions = []
        
        self.density.reset_transactions()
        self.diversity.reset_transactions()
        self.uniqueness.reset_transactions()

class Transaction:
    def __init__(self, name, is_error, activity_array):
        self.name = name
        self.is_error = is_error
        self.activity = activity_array
        self.hash_code = hash(str(self.activity))
        
class NormalizedRho:
    def __init__(self, nr_components):
        self.activity_counter = 0
        self.nr_components = nr_components

    def update_transactions(self, transaction):
        activity = np.count_nonzero(transaction.activity)
        self.activity_counter += activity
        
        self.last_activity = activity
    
    def revoke_transaction(self, transaction):
        self.activity_counter -= self.last_activity

    def reset_transactions(self):
        self.activity_counter = 0

    def calculate_density(self, nr_transactions):
        rho = self.activity_counter / (self.nr_components * nr_transactions) if nr_transactions != 0 else 0
        normalized_rho = 1 - abs(1 - 2 * rho)
        
        return normalized_rho
    

class GiniSimpson:
    def __init__(self):
        self.species = {}

    def update_transactions(self, transaction):
        if transaction.hash_code in self.species:
            self.species[transaction.hash_code] = self.species[transaction.hash_code] + 1
        else:
            self.species[transaction.hash_code] = 1

    def revoke_transaction(self, transaction):
        self.species[transaction.hash_code] = self.species[transaction.hash_code] - 1

    def reset_transactions(self):
        self.species = {}

    def calculate_diversity(self):
        N = 0
        n = 0

        for s in self.species.keys():
            ni = self.species[s]
            N += ni
            n += (ni * (ni - 1))
        
        diversity = 1 if (N == 0 or (N-1 == 0)) else n / (N * (N-1))
        gini_simpson = 1 - diversity
        return gini_simpson


class Ambiguity:
    def __init__(self, nr_components):
        self.involvement_matrix = np.empty((nr_components, 0), bool)
        self.nr_components = nr_components
        
    def update_transactions(self, transaction):
        self.involvement_matrix = np.concatenate((self.involvement_matrix, transaction.activity.T), axis=1)

    def revoke_transaction(self, transaction):
        self.involvement_matrix = np.delete(self.involvement_matrix, -1, axis=1)

    def reset_transactions(self):
        self.involvement_matrix = np.empty((self.nr_components, 0), bool)


    def calculate_uniqueness(self, nr_transactions):
        start = time.time()
        ambiguity_groups = np.unique(self.involvement_matrix, axis = 0)
        end = time.time()
        #print("took",end - start)
        ambiguity = len(ambiguity_groups) / self.nr_components
        return ambiguity