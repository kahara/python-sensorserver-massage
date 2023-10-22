"""See https://github.com/MrCredulous/1D-MCTV-Denoising"""
# pylint: disable=R0205,C0103,C0116,R0903,R0912,R0915
import numpy as np

# FIXME clean this up further


class Parameter(object):
    """..."""

    def __init__(self, re, it, co, no):
        self.regularization = re
        self.most_iter_num = it
        self.convergence = co
        self.nonconvexity = no

    def print_value(self):
        print(self.regularization, self.most_iter_num, self.convergence, self.nonconvexity)


def denoise_1d_tv(Y, lamda):

    N = len(Y)
    X = np.zeros(N)

    k, k0, kz, kf = 0, 0, 0, 0
    vmin = Y[0] - lamda
    vmax = Y[0] + lamda
    umin = lamda
    umax = -lamda

    while k < N:

        if k == N - 1:
            X[k] = vmin + umin
            break

        if Y[k + 1] < vmin - lamda - umin:
            for i in range(k0, kf + 1):
                X[i] = vmin
            k, k0, kz, kf = kf + 1, kf + 1, kf + 1, kf + 1
            vmin = Y[k]
            vmax = Y[k] + 2 * lamda
            umin = lamda
            umax = -lamda

        elif Y[k + 1] > vmax + lamda - umax:
            for i in range(k0, kz + 1):
                X[i] = vmax
            k, k0, kz, kf = kz + 1, kz + 1, kz + 1, kz + 1
            vmin = Y[k] - 2 * lamda
            vmax = Y[k]
            umin = lamda
            umax = -lamda

        else:
            k += 1
            umin = umin + Y[k] - vmin
            umax = umax + Y[k] - vmax
            if umin >= lamda:
                vmin = vmin + (umin - lamda) * 1.0 / (k - k0 + 1)
                umin = lamda
                kf = k
            if umax <= -lamda:
                vmax = vmax + (umax + lamda) * 1.0 / (k - k0 + 1)
                umax = -lamda
                kz = k

        if k == N - 1:
            if umin < 0:
                for i in range(k0, kf + 1):
                    X[i] = vmin
                k, k0, kf = kf + 1, kf + 1, kf + 1
                vmin = Y[k]
                umin = lamda
                umax = Y[k] + lamda - vmax

            elif umax > 0:
                for i in range(k0, kz + 1):
                    X[i] = vmax
                k, k0, kz = kz + 1, kz + 1, kz + 1
                vmax = Y[k]
                umax = -lamda
                umin = Y[k] - lamda - vmin

            else:
                for i in range(k0, N):
                    X[i] = vmin + umin * 1.0 / (k - k0 + 1)
                break

    return X


def denoise_1d_metv(Y, para):

    K, N = 0, len(Y)
    X = np.zeros(N)
    U = np.ones(N)
    lamda, alpha = para.regularization, para.nonconvexity
    num, err = para.most_iter_num, para.convergence

    while K <= num and np.linalg.norm(U - X) > err:

        Z = Y + lamda * alpha * (X - denoise_1d_tv(Y, 1 / alpha))
        U = X
        X = denoise_1d_tv(Z, lamda)
        K += 1

    return X


def denoise_1d_mctv(Y, para):

    K, N = 0, len(Y)
    X = np.zeros(N)
    U = np.ones(N)
    lamda, alpha = para.regularization, para.nonconvexity
    num, err = para.most_iter_num, para.convergence

    def shrink(Y, lamda):
        return np.fmax(np.fabs(Y) - lamda, 0) * np.sign(Y)

    def Dx(Y):
        return np.ediff1d(Y, to_begin=Y[0] - Y[-1])

    def Dxt(Y):
        X = np.ediff1d(Y[::-1])[::-1]
        return np.append(X, Y[-1] - Y[0])

    while K <= num and np.linalg.norm(U - X) > err:

        C = Dxt(Dx(X)) - Dxt(shrink(Dx(X), 1 / alpha))
        Z = Y + lamda * alpha * C
        U = X
        X = denoise_1d_tv(Z, lamda)
        K += 1

    return X
