__author__ = "PedroCR"

import numpy as np
import pandas as pd
from mortality_table import MortalityTable


class CommutationFunctions(MortalityTable):
    '''
    Instantiates a for a specific mortality table and interest rate, all the usual commutation functions.
    '''

    def __init__(self, i=None, g=0, data_type='q', mt=None, perc=100, app_cont=False):
        MortalityTable.__init__(self, data_type, mt, perc)
        if i is None:
            return
        self.i = i / 100.
        self.g = g / 100.
        self.v = 1 / (1 + self.i)
        self.d = (1 + self.g) / (1 + self.i)
        self.app_cont = app_cont
        self.cont = np.sqrt(1 + self.i)

        # self.Dx = np.array([self.lx[x] * np.power(self.d, x) for x in range(len(self.lx))])
        self.Dx = self.lx[:-1] * np.power(self.d, range(len(self.lx[:-1])))
        self.Nx = np.array([np.sum(self.Dx[x:]) for x in range(len(self.lx[:-1]))])
        self.Cx = self.dx * np.power(self.d, range(1, len(self.dx) + 1))
        self.Mx = np.array([np.sum(self.Cx[x:]) for x in range(len(self.Cx))])
        if self.app_cont:
            self.Mx = self.Mx * self.cont

    def df_commutation_table(self):
        data = {'Dx': self.Dx, 'Nx': self.Nx, 'Cx': self.Cx, 'Mx': self.Mx}
        df = pd.DataFrame(data)
        data_lf = self.df_life_table()
        df = pd.concat([data_lf, df], axis=1, sort=False)  # todo
        return df

    # life insurances
    def nEx(self, x, n):
        """
        Pure endowment or Deferred capital
        :param x: age at the beginning of the contract
        :param n: years until payment, if x is alive
        :return: the present value of a pure endowment of 1 at age x+n
        """
        if x < 0:
            return np.nan
        if n <= 0:
            return 1
        if x + n > self.w:
            return 0.
        D_x = self.Dx[x]
        D_x_n = self.Dx[x + n]
        self.msn.append(f"{n}_E_{x}={D_x_n} / {D_x}")
        return D_x_n / D_x

    def Ax(self, x):
        """
        Whole life insurance
        :param x: age at the beginning of the contract
        :return: Expected Present Value (EPV) of a whole life insurance (i.e. net single premium), that pays 1,at the
        end of the year of death. It is also commonly referred to as the Actuarial Value or Actuarial Present Value.
        """
        if x < 0:
            return np.nan
        if x > self.w:
            return self.v  # it will die before year's end, because already attained age>w
        D_x = self.Dx[x]
        if self.app_cont:
            M_x = self.Mx[x] / self.cont
        else:
            M_x = self.Mx[x]
        self.msn.append(f"A_{x}={M_x} / {D_x}")
        return M_x / D_x

    def Ax_(self, x):
        """
        Whole life insurance
        :param x: age at the beginning of the contract
        :return: Expected Present Value (EPV) of a whole life insurance (i.e. net single premium), that pays 1, at the
        moment of death. It is also commonly referred to as the Actuarial Value or Actuarial Present Value.
        """
        if x < 0:
            return np.nan
        if x > self.w:  # it will die before year's end, because already attained age>w
            return self.v ** .5
        D_x = self.Dx[x]
        if self.app_cont:
            M_x = self.Mx[x]
        else:
            M_x = self.Mx[x] * self.cont
        self.msn.append(f"A_{x}_={M_x} / {D_x}")
        return M_x / D_x

    def nAx(self, x, n):
        """
        Term life insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :return: Expected Present Value (EPV) of a term (temporary) life insurance (i.e. net single premium), that
        pays 1, at the end of the year of death. It is also commonly referred to as the Actuarial Value or
        Actuarial Present Value.
        """
        if x < 0:
            return np.nan
        if n < 0:
            return np.nan
        if x + n > self.w:
            return self.Ax(x)
        D_x = self.Dx[x]
        if self.app_cont:
            M_x = self.Mx[x] / self.cont
            M_x_n = self.Mx[x + n] / self.cont
        else:
            M_x = self.Mx[x]
            M_x_n = self.Mx[x + n]
        self.msn.append(f"{n}_A_{x}=({M_x}-{M_x_n}) / {D_x}")
        return (M_x - M_x_n) / D_x

    def nAx_(self, x, n):
        """
        Term life insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :return: Expected Present Value (EPV) of a term (temporary) life insurance (i.e. net single premium), that
        pays 1, at the moment of death. It is also commonly referred to as the Actuarial Value or
        Actuarial Present Value.
        """
        if x < 0:
            return np.nan
        if n < 0:
            return np.nan
        if x + n > self.w:
            return self.Ax(x)
        D_x = self.Dx[x]
        if self.app_cont:
            M_x = self.Mx[x]
            M_x_n = self.Mx[x + n]
        else:
            M_x = self.Mx[x] * self.cont
            M_x_n = self.Mx[x + n] * self.cont
        self.msn.append(f"{n}_A_{x}_=({M_x}-{M_x_n}) / {D_x}")
        return (M_x - M_x_n) / D_x

    def nAEx(self, x, n):
        """
        Endowment insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :return: Expected Present Value (EPV) of an Endowment life insurance (i.e. net single premium), that
        pays 1, at the end of year of death or 1 if x survives to age x+n. It is also commonly referred to as the
        Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{n}_AE_{x}={n}_A_{x}+{n}_E_{x}")
        return self.nAx(x, n) + self.nEx(x, n)

    def nAEx_(self, x, n):
        """
        Endowment insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :return: Expected Present Value (EPV) of an Endowment life insurance (i.e. net single premium), that
        pays 1, at the moment of death or 1 if x survives to age x+n. It is also commonly referred to as the
        Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{n}_AE_{x}_={n}_A_{x}_+{n}_E_{x}")
        return self.nAx_(x, n) + self.nEx(x, n)

    # deferred life insurances
    def t_Ax(self, x, defer=0):
        """
        Deferred Whole life insurance
        :param x: age at the beginning of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of a whole life insurance (i.e. net single premium), that pays 1,at the
        end of the year of death. It is also commonly referred to as the Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{defer}|_A_{x}={defer}_E_{x}*A_{x + defer}")
        return self.nEx(x, defer) * self.Ax(x + defer)

    def t_Ax_(self, x, defer=0):
        """
        Deferred Whole life insurance
        :param x: age at the beginning of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of a whole life insurance (i.e. net single premium), that pays 1, at the
        moment of death. It is also commonly referred to as the Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{defer}|_A_{x}_={defer}_E_{x}*A_{x + defer}_")
        return self.nEx(x, defer) * self.Ax_(x + defer)

    def t_nAx(self, x, n, defer=0):
        """
        Deferred Term life insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of a term (temporary) life insurance (i.e. net single premium), that
        pays 1, at the end of the year of death. It is also commonly referred to as the Actuarial Value or
        Actuarial Present Value.
        """
        self.msn.append(f"{defer}|{n}_A_{x}={defer}_E_{x}*{n}_A_{x + defer}")
        return self.nEx(x, defer) * self.nAx(x + defer, n)

    def t_nAx_(self, x, n, defer=0):
        """
        Deferred Term life insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of a term (temporary) life insurance (i.e. net single premium), that
        pays 1, at the moment of death. It is also commonly referred to as the Actuarial Value or
        Actuarial Present Value.
        """
        self.msn.append(f"{defer}|{n}_A_{x}_={defer}_E_{x}*{n}_A_{x + defer}_")
        return self.nEx(x, defer) * self.nAx_(x + defer, n)

    def t_nAEx(self, x, n, defer=0):
        """
        Deferred Endowment insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of an Endowment life insurance (i.e. net single premium), that
        pays 1, at the end of year of death or 1 if x survives to age x+n. It is also commonly referred to as the
        Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{defer}|{n}_AE_{x}={defer}_E_{x}*{n}_AE_{x + defer}")
        return self.nEx(x, defer) * self.nAEx(x + defer, n)

    def t_nAEx_(self, x, n, defer=0):
        """
        Deferred Endowment insurance
        :param x: age at the beginning of the contract
        :param n: period of the contract
        :param defer: deferment period
        :return: Expected Present Value (EPV) of an Endowment life insurance (i.e. net single premium), that
        pays 1, at the moment of death or 1 if x survives to age x+n. It is also commonly referred to as the
        Actuarial Value or Actuarial Present Value.
        """
        self.msn.append(f"{defer}|{n}_AE_{x}={defer}_E_{x}*{n}_AE_{x + defer}_")
        return self.nEx(x, defer) * self.nAEx_(x + defer, n)

    # life annuities
    def ax(self, x, m=1):
        """
        axn : Return the actuarial present value of a (immediate) temporal (term certain) annuity: n-year temporary
        life annuity-late. Payable 'm' per year at the ends of the period
        :param x: age at the beginning of the contract
        :param m: number of payments per period used to quote the interest rate
        :return:Expected Present Value (EPV) for payments of 1/m
        """
        if x < 0:
            return np.nan
        if m < 0:
            return np.nan

        return self.Nx[x + 1] / self.Dx[x] + float(m - 1) / float(m * 2) # todo confirmar

    def aax(self, x, m=1):
        """
        äxn : Return the actuarial present value of a (immediate) temporal (term certain) annuity: n-year temporary
        life annuity-anticipatory. Payable 'm' per year at the beginning of the period
        :param x: age at the beginning of the contract
        :param m: number of payments per period used to quote the interest rate
        :return:Expected Present Value (EPV) for payments of 1/m
        """
        pass
