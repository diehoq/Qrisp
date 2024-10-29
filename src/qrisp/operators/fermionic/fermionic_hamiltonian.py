"""
\********************************************************************************
* Copyright (c) 2024 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""
from qrisp.operators import Hamiltonian
from qrisp.operators.fermionic.fermionic_term import FermionicTerm
from qrisp.operators.fermionic.transformations import *
#from qrisp.operators.pauli.pauli_term import PauliTerm
#from qrisp.operators.pauli.pauli_hamiltonian import PauliHamiltonian

import sympy as sp

from sympy import init_printing
# Initialize automatic LaTeX rendering
init_printing()

threshold = 1e-9

#
# FermionicHamiltonian
#

class FermionicHamiltonian(Hamiltonian):
    r"""
    This class provides an efficient implementation of ladder_term operators, i.e.,
    operators of the form

    .. math::
        
        H=\sum\limits_{j}\alpha_jA_j 
            
    where each term $A_j$ is a product of fermionic raising $a_i^{\dagger}$ and lowering $a_i$ operators acting on the $i$ th fermionic mode.

    The ladder operators satisfy the commutation relations

    .. math::

        \{a_i,a_j^{\dagger}\} &= a_ia_j^{\dagger}+a_j^{\dagger}a_i = \delta_{ij}\\
        \{a_i^{\dagger},a_j^{\dagger}\} &= \{a_i,a_j\} = 0

    Examples
    --------

    A ladder term operator can be specified conveniently in terms of ``a`` (lowering, i.e., annihilation), ``c`` (raising, i.e., creation) operators:

    ::
        
        from qrisp.operators.fermionic import a, c

        H = a(2)*c(1)+a(3)*c(2)
        H

    Yields $a_2c_1+a_3c_2$.

    """

    def __init__(self, terms_dict={}, avoid_flips = True):
        
        self.terms_dict = terms_dict

    def reduce(self):
        
        # This function performs some non trivial logic.
        
        # The problem here is that each fermionic term can
        # be reshaped into several different forms and still express
        # the same operator. 
        # For instance, the operator can be arbitrarily reordered
        # if the permutation sign is take care of and no creators/annihilators
        # with the same index are swapped.
        # Furthermore the Hamiltonian must be Hermitian, so each
        # term must be equivalent to is Hermitian conjugate.
        
        # This function implements a storage system, that combines
        # the coefficients of differing terms representing the same operator
        # into a single term.
        
        # This dictionary will contain the new terms, where redundancies
        # are taken care of.
        new_terms_dict = {}
        
        for term, coeff in self.terms_dict.items():
            
            # We only store the sorted version of each term.
            # Sorting here means permuting the creators/annihilators
            # while considering the sign of the permutation applied by the sort.
            # The sort is performed in a stable manner, so terms like a(0)*c(0)
            # don't get permuted (this would be a non-trivial anti-commutator).
            sorted_term, flip_sign = term.sort()
            if sorted_term not in new_terms_dict:
                # If the sorted term is not in the terms dict, the sorted version
                # of the daggering might be.
                daggered_sorted_term, daggered_flip_sign = term.dagger().sort()
                if daggered_sorted_term in new_terms_dict:
                    sorted_term = daggered_sorted_term
                    flip_sign = daggered_flip_sign
                    
                # If neither the daggered nor the non-daggered term are available
                # in some situations, we can choose which one we want to store.
                # To improve readability, we store the term which has no minus-sign.
                # Note that this is only valid in certain situations.
                # When multiplying terms, this type of transformations causes
                # problems. Because of this the avoid_flips keyword is set to 
                # False within __mul__
                # elif flip_sign < 0 and avoid_flips:
                #     sorted_term = daggered_sorted_term
                #     flip_sign = daggered_flip_sign
            
            # Compute the new coefficient.
            new_terms_dict[sorted_term] = flip_sign*coeff + new_terms_dict.get(sorted_term, 0)
            
        self.terms_dict = new_terms_dict

    def len(self):
        return len(self.terms_dict)
    
    #
    # Printing
    #

    def _repr_latex_(self):
        # Convert the sympy expression to LaTeX and return it
        expr = self.to_expr()
        return f"${sp.latex(expr)}$"
    
    def __str__(self):
        # Convert the sympy expression to a string and return it
        expr = self.to_expr()
        return str(expr)
    
    def to_expr(self):
        """
        Returns a SymPy expression representing the operator.

        Returns
        -------
        expr : sympy.expr
            A SymPy expression representing the operator.

        """
        
        expr = 0  
        for ladder_term,coeff in self.terms_dict.items():
            term = ladder_term.to_expr()
            term_dg =  + ladder_term.dagger().to_expr()
            if coeff not in [2, -2]:
                term *= coeff/2
                term_dg *= coeff/2
            elif coeff == -2:
                expr += -term - term_dg
                continue
            expr += term + term_dg
        return expr

    #
    # Arithmetic
    #
    
    def __eq__(self, other):
        
        if len(self.terms_dict) != len(other.terms_dict):
            return False
        
        for term, coeff in self.terms_dict.items():
            if not term in other.terms_dict:
                daggered_sorted_term, flip_sign = term.dagger().sort()
                if daggered_sorted_term not in other.terms_dict:
                    return False
                elif self.terms_dict[term] != flip_sign*other.terms_dict[daggered_sorted_term]:
                    return False
                continue
                    
            if self.terms_dict[term] != other.terms_dict[term]:
                return False
        
        return True
    
    def __neg__(self):
        return -1*self
            
    #def __pow__(self, e):
    #    if self.len()==1:
    #        if isinstance(e, int) and e>=0:
    #            if e%2==0:
    #                return FermionicHamiltonian({FermionicTerm():1})
    #            else:
    #                return self
    #        else:
    #            raise TypeError("Unsupported operand type(s) for ** or pow(): "+str(type(self))+" and "+str(type(e)))
    #    else:
    #        raise TypeError("Unsupported operand type(s) for ** or pow(): "+str(type(self))+" and "+str(type(e)))

    def __add__(self,other):
        """
        Returns the sum of the operator self and other.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to add to the operator self.

        Returns
        -------
        result : FermionicHamiltonian
            The sum of the operator self and other.

        """

        if isinstance(other,(int,float,complex)):
            other = FermionicHamiltonian({FermionicTerm():other})
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot add FermionicHamiltonian and "+str(type(other)))

        res_terms_dict = {}

        for ladder_term,coeff in self.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)+coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
    
        for ladder_term,coeff in other.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)+coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
        
        result = FermionicHamiltonian(res_terms_dict)
        return result
    
    def __sub__(self,other):
        """
        Returns the difference of the operator self and other.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to substract from the operator self.

        Returns
        -------
        result : FermionicHamiltonian
            The difference of the operator self and other.

        """

        if isinstance(other,(int,float,complex)):
            other = FermionicHamiltonian({FermionicTerm():other})
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot substract FermionicHamiltonian and "+str(type(other)))

        res_terms_dict = {}

        for ladder_term,coeff in self.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)+coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
    
        for ladder_term,coeff in other.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)-coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
        
        result = FermionicHamiltonian(res_terms_dict)
        return result
    
    def __rsub__(self,other):
        """
        Returns the difference of the operator other and self.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to substract from the operator self from.

        Returns
        -------
        result : FermionicHamiltonian
            The difference of the operator other and self.

        """

        if isinstance(other,(int,float,complex)):
            other = FermionicHamiltonian({FermionicTerm():other})
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot substract FermionicHamiltonian and "+str(type(other)))

        res_terms_dict = {}

        for ladder_term,coeff in self.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)-coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
    
        for ladder_term,coeff in other.terms_dict.items():
            res_terms_dict[ladder_term] = res_terms_dict.get(ladder_term,0)+coeff
            if abs(res_terms_dict[ladder_term])<threshold:
                del res_terms_dict[ladder_term]
        
        result = FermionicHamiltonian(res_terms_dict)
        return result

    def __mul__(self,other):
        """
        Returns the product of the operator self and other.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to multiply with the operator self.

        Returns
        -------
        result : FermionicHamiltonian
            The product of the operator self and other.

        """

        if isinstance(other,(int,float,complex)):
            other = FermionicHamiltonian({FermionicTerm():other})
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot multipliy FermionicHamiltonian and "+str(type(other)))

        res_terms_dict = {}

        for ladder_term1, coeff1 in self.terms_dict.items():
            for ladder_term2, coeff2 in other.terms_dict.items():
                curr_ladder_term = ladder_term1*ladder_term2
                res_terms_dict[curr_ladder_term] = res_terms_dict.get(curr_ladder_term,0) + coeff1*coeff2

        result = FermionicHamiltonian(res_terms_dict, avoid_flips = False)
        return result

    __radd__ = __add__
    __rmul__ = __mul__

    #
    # Inplace arithmetic
    #

    def __iadd__(self,other):
        """
        Adds other to the operator self.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to add to the operator self.

        """

        if isinstance(other,(int,float,complex)):
            self.terms_dict[FermionicTerm()] = self.terms_dict.get(FermionicTerm(),0)+other
            return self
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot add FermionicHamiltonian and "+str(type(other)))

        for ladder_term,coeff in other.terms_dict.items():
            self.terms_dict[ladder_term] = self.terms_dict.get(ladder_term,0)+coeff
            if abs(self.terms_dict[ladder_term])<threshold:
                del self.terms_dict[ladder_term]
        self.terms_dict = FermionicHamiltonian(self.terms_dict).terms_dict
        return self         

    def __isub__(self,other):
        """
        Substracts other from the operator self.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to substract from the operator self.

        """

        if isinstance(other,(int,float,complex)):
            self.terms_dict[FermionicTerm()] = self.terms_dict.get(FermionicTerm(),0)-other
            return self
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot add FermionicHamiltonian and "+str(type(other)))

        for ladder_term,coeff in other.terms_dict.items():
            self.terms_dict[ladder_term] = self.terms_dict.get(ladder_term,0)-coeff
            if abs(self.terms_dict[ladder_term])<threshold:
                del self.terms_dict[ladder_term]  
        return self
    
    def __imul__(self,other):
        """
        Multiplys other to the operator self.

        Parameters
        ----------
        other : int, float, complex or FermionicHamiltonian
            A scalar or a FermionicHamiltonian to multiply with the operator self.

        """

        if isinstance(other,(int,float,complex)):
            other = FermionicHamiltonian({FermionicTerm():other})
        if not isinstance(other,FermionicHamiltonian):
            raise TypeError("Cannot multipliy FermionicHamiltonian and "+str(type(other)))

        res_terms_dict = {}

        for ladder_term1, coeff1 in self.terms_dict.items():
            for ladder_term2, coeff2 in other.terms_dict.items():
                curr_ladder_term = ladder_term1*ladder_term2
                res_terms_dict[curr_ladder_term] = res_terms_dict.get(curr_ladder_term,0) + coeff1*coeff2

        self.terms_dict = res_terms_dict    

    #
    # Miscellaneous
    #

    def apply_threshold(self,threshold):
        """
        Removes all ladder_term terms with coefficient absolute value below the specified threshold.

        Parameters
        ----------
        threshold : float
            The threshold for the coefficients of the ladder_term terms.

        """

        delete_list = []
        for ladder_term,coeff in self.terms_dict.items():
            if abs(coeff)<threshold:
                delete_list.append(ladder_term)
        for ladder_term in delete_list:
            del self.terms_dict[ladder_term]

    #def to_sparse_matrix(self):
        """
        Returns a matrix representing the operator.
    
        Returns
        -------
        M : scipy.sparse.csr_matrix
            A sparse matrix representing the operator.

        """
        

    def ground_state_energy(self):
        """
        Calculates the ground state energy (i.e., the minimum eigenvalue) of the operator classically.
    
        Returns
        -------
        E : float
            The ground state energy. 

        """
        pass

    #
    # Transformations
    #

    def to_pauli_hamiltonian(self, mapping='jordan_wigner'):
        """
        Transforms the fermionic Hamiltonian to a :ref:`PauliHamiltonian`.

        Parameters
        ----------
        mapping : str, optional
            The mapping to transform the Hamiltonian. Available is ``jordan_wigner``.
            The default is ``jordan_wigner``.

        Returns
        -------
        H : :ref:`PauliHamiltonian``
            The resulting Pauli Hamiltonian.
        
        """

        H = 0
        for term,coeff in self.terms_dict.items():

            h = coeff/2
            for ladder in term.ladder_list[::-1]:
                h *= jordan_wigner(ladder)
            H += h

            h = coeff/2
            for ladder in term.dagger().ladder_list[::-1]:
                h *= jordan_wigner(ladder)
            H += h

        jordan_wigner.cache_clear()

        return H
    
    #
    # Partitions 
    #

    #
    # Trotterization
    #

    def trotterization(self, qarg, t = 1, steps = 1, iter = 1):
        r"""
        Returns a function for performing Hamiltonian simulation, i.e., approximately implementing the unitary operator $e^{itH}$ via Trotterization.

        Returns
        -------
        U : function 
            A Python function that implements the first order Suzuki-Trotter formula.
            Given a Hamiltonian $H=H_1+\dotsb +H_m$ the unitary evolution $e^{itH}$ is 
            approximated by 
            
            .. math::

                e^{itH}\approx U_1(t,N)=\left(e^{iH_1t/N}\dotsb e^{iH_mt/N}\right)^N

            This function recieves the following arguments:

            * qarg : QuantumVariable or QuantumArray
                The quantum argument.
            * t : float, optional
                The evolution time $t$. The default is 1.
            * steps : int, optional
                The number of Trotter steps $N$. The default is 1.
            * iter : int, optional 
                The number of iterations the unitary $U_1(t,N)$ is applied. The default is 1.
        
        """
        
        self.reduce()
        for i in range(iter):
            for j in range(steps):
                for ferm_term, value in self.terms_dict.items():
                    ferm_term.simulate(value*t/steps, qarg)