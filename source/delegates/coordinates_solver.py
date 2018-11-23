# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 11:24:12 2017

@author: quentinpeter
"""
import numpy as np
from scipy import optimize
import warnings
from errors import CoordinatesError


def get_matrices(ax, ay, az, am):
    """Get the rotations matrix along the X, Y, and Z axis,
    As well as the matrix for XY stage angle"""
    c, s = np.cos(ax), np.sin(ax)
    Rx = np.array([[1, 0, 0],
                   [0, c, -s],
                   [0, s, c]])

    c, s = np.cos(ay), np.sin(ay)
    Ry = np.array([[c, 0, s],
                   [0, 1, 0],
                   [-s, 0, c]])

    c, s = np.cos(az), np.sin(az)
    Rz = np.array([[c, -s, 0],
                   [s, c, 0],
                   [0, 0, 1]])

    c, s = np.cos(am), np.sin(am)
    Rm = np.array([[1, s, 0],
                   [0, c, 0],
                   [0, 0, 1]])

    return Rx, Ry, Rz, Rm


def get_d_matrices(ax, ay, az, am):
    """Get the derivatives of get_matrices matrices"""
    c, s = np.cos(ax), np.sin(ax)
    Rx = np.array([[0, 0, 0],
                   [0, -s, -c],
                   [0, c, -s]])

    c, s = np.cos(ay), np.sin(ay)
    Ry = np.array([[-s, 0, c],
                   [0, 0, 0],
                   [-c, 0, -s]])

    c, s = np.cos(az), np.sin(az)
    Rz = np.array([[-s, -c, 0],
                   [c, -s, 0],
                   [0, 0, 0]])

    c, s = np.cos(am), np.sin(am)
    Rm = np.array([[0, c, 0],
                   [0, -s, 0],
                   [0, 0, 0]])

    return Rx, Ry, Rz, Rm


def XstoXm(Xs, offset, rotation_angles):
    """Transform from stage to master coordinates"""
    Xs = np.asarray(Xs)
    offset = np.asarray(offset)
    Rx, Ry, Rz, Rm = get_matrices(*rotation_angles)
    R = Rx@Ry@Rz@Rm
    return (R@Xs.T).T - offset


def XmtoXs(Xm, offset, rotation_angles):
    """Transform from master to stage coordinates"""
    Xm = np.asarray(Xm)
    offset = np.asarray(offset)
    Rx, Ry, Rz, Rm = get_matrices(*rotation_angles)
    R = Rx@Ry@Rz@Rm
    return (np.linalg.inv(R)@(Xm + offset).T).T


def single_angle(angles):
    """Transform the angles to be contained between -pi and +pi"""
    angles %= 2 * np.pi
    angles[angles > np.pi] -= 2 * np.pi
    return angles


def is_collinear(Xs):
    vector_diff = np.diff(Xs, axis=0)
    is_collinear = np.max(np.abs(np.cross(vector_diff[np.newaxis],
                                          vector_diff[:, np.newaxis]))) < 1e-5
    return is_collinear


def solve_xyz(Xstage, Xmaster, *,
              offset=None, rotation_angles=None,
              offset_var=None, angle_var=None):
    """Find the best offset and angles to go from Xs to Xm
    Give at least 3 non-collinear points. Otherwise approximate."""

    # Check inputs
    if np.shape(Xstage) != np.shape(Xmaster):
        raise CoordinatesError("Shapes not matching.")

    if offset is None:
        offset = np.zeros(3)
    else:
        offset = np.asarray(offset)

    if rotation_angles is None:
        rotation_angles = np.zeros(4)
    else:
        rotation_angles = np.asarray(rotation_angles)

    # Take care of low number of input / collinearity
    N = len(Xmaster)
    if N == 0:
        return offset, rotation_angles

    elif N == 1:
        offset = Xstage[0] - Xmaster[0]
        return offset, rotation_angles

    elif is_collinear(Xmaster):
        if N > 2:
            warnings.warn(RuntimeWarning("Collinear data."))
        # Want only rotation z
        angle_var = np.array([2])

    # Check which are the variables
    if offset_var is None:
        offset_var = np.arange(3)

    if angle_var is None:
        angle_var = np.arange(4)

    Nvar = len(offset_var) + len(angle_var)

    # Define minimisation function and jacobian
    def fun(x, Xs, Xm):
        """Least square error"""
        offset[offset_var] = np.asarray(x[:len(offset_var)])
        rotation_angles[angle_var] = np.asarray(x[len(offset_var):])
        Xm2 = XstoXm(Xs, offset, rotation_angles)
        return np.sqrt(np.mean(np.square(Xm2 - Xm)))

    def jac(x, Xs, Xm):
        """Jacobian matrix of fun"""
        offset[offset_var] = np.asarray(x[:len(offset_var)])
        rotation_angles[angle_var] = np.asarray(x[len(offset_var):])

        residual = fun(x, Xs, Xm)
        if residual == 0:
            return np.zeros(Nvar)

        Rs = get_matrices(*rotation_angles)
        dRs = get_d_matrices(*rotation_angles)
        Xm2 = XstoXm(Xs, offset, rotation_angles)
        ret = np.zeros(Nvar)
        j = 0
        for i in offset_var:
            v = np.zeros(3)
            v[i] = -1
            ret[j] = (np.mean((Xm2 - Xm) * v))
            j = j + 1

        for i in angle_var:
            tmpRs = np.array(Rs)
            tmpRs[i] = dRs[i]
            ret[j] = (np.mean((Xm2 - Xm) *
                              (tmpRs[0]@tmpRs[1]@tmpRs[2]@tmpRs[3]@Xs.T).T))
            j = j + 1

        ret = 1 / residual * ret
        return np.asarray(ret)

    # Minimise with scipy
    res = optimize.minimize(fun, np.zeros(
        Nvar), args=(Xstage, Xmaster), jac=jac)
#    if not res.success:
#        warnings.warn(RuntimeWarning("Minimisation unsuccessful."))
    offset[offset_var] = np.asarray(res.x[:len(offset_var)])
    rotation_angles[angle_var] = np.asarray(res.x[len(offset_var):])

    # Get unique angles
    rotation_angles = single_angle(rotation_angles)

    # This one should only be used if all the Xm are on the same plane as the
    # Z axis is swapped
    if np.abs(rotation_angles[3]) > np.pi / 2:
        if np.max(np.diff(Xmaster[..., 2])) > 1e-3:
            raise CoordinatesError("The dimentions are swapped?")
        rotation_angles[0] = -rotation_angles[0]
        rotation_angles[1] = -rotation_angles[1] + np.pi
        rotation_angles[2] = -rotation_angles[2] + np.pi
        rotation_angles[3] = -rotation_angles[3] + np.pi
        rotation_angles = single_angle(rotation_angles)
        offset[2] = -offset[2]

    # This is a symmetry of the system
    if np.abs(rotation_angles[0]) > np.pi / 2:
        rotation_angles[0] = rotation_angles[0] + np.pi
        rotation_angles[1] = -rotation_angles[1] + np.pi
        rotation_angles[2] = rotation_angles[2] + np.pi
        rotation_angles[3] = rotation_angles[3]
        rotation_angles = single_angle(rotation_angles)

    # Can probably remove, check the transformation hasn't changed anything
    x = [*offset[offset_var], *rotation_angles[angle_var]]
    if np.abs(fun(x, Xstage, Xmaster) - res.fun) > 1e-9:
        raise CoordinatesError('Similarity changed result!')

    return offset, rotation_angles


def solve_colinear(Xstage, Xmaster):
    pass


def solve_z(Xstage, *, offset=None, rotation_angles=None):
    """Get correction such as all the given points are on a plane
    The Z rotation, XY Stage correction, and XY offset can be given."""
    Xstage = np.asarray(Xstage)
    # Create output
    if offset is None:
        offset = np.zeros(3)
    else:
        offset = np.asarray(offset)

    if rotation_angles is None:
        rotation_angles = np.zeros(4)
    else:
        rotation_angles = np.asarray(rotation_angles)

    # If we have less than 3 points, just take the mean
    N = len(Xstage)
    if N == 0:
        return offset, rotation_angles

    elif N < 3:
        # Only correct the Z offset
        offset[2] = np.mean(Xstage[:, 2], 0)
        return offset, rotation_angles

    elif is_collinear(Xstage):
        # Only correct the Z offset
        warnings.warn(RuntimeWarning("Collinear data."))
        offset[2] = np.mean(Xstage[:, 2], 0)
        return offset, rotation_angles

    # Define the optimisation function and jacobian
    def fun(x, Xs):
        offset[2] = x[0]
        rotation_angles[:2] = np.asarray(x[1:])

        Xm = XstoXm(Xs, offset, rotation_angles)
        return np.sqrt(np.mean(np.square(Xm[..., 2])))

    def jac(x, Xs):

        offset[2] = x[0]
        rotation_angles[:2] = np.asarray(x[1:])

        Xm = XstoXm(Xs, offset, rotation_angles)

        residual = fun(x, Xs)

        if residual == 0:
            return np.zeros(3)

        Rs = get_matrices(*rotation_angles)
        dRs = get_d_matrices(*rotation_angles)

        ret = np.zeros(3)

        ret[0] = (2 * np.mean((Xm[..., 2]) * -1))

        for i in range(2):
            tmpRs = np.array(Rs)
            tmpRs[i] = dRs[i]
            ret[i + 1] = (2 * np.mean(Xm[..., 2] *
              (tmpRs[0]@tmpRs[1]@tmpRs[2]@tmpRs[3]@Xs.T).T[..., 2]))

        ret = 1 / residual * ret
        return np.asarray(ret)

    # Optimise with scipy
    res = optimize.minimize(fun, np.zeros(3), args=(Xstage), jac=jac)
#    if not res.success:
#        warnings.warn(RuntimeWarning("Minimisation unsuccessful."))

    offset[2] = res.x[0]
    rotation_angles[:2] = np.asarray(res.x[1:])

    rotation_angles = single_angle(rotation_angles)

    # Check for symmetries
    if np.abs(rotation_angles[0]) > np.pi / 2:
        rotation_angles[0] = rotation_angles[0] + np.pi
        rotation_angles[1] = -rotation_angles[1]
        offset[2] = -offset[2]
        rotation_angles = single_angle(rotation_angles)

    if np.abs(rotation_angles[1]) > np.pi / 2:
        rotation_angles[1] = rotation_angles[1] + np.pi
        offset[2] = -offset[2]
        rotation_angles = single_angle(rotation_angles)

    return offset, rotation_angles


if __name__ == "__main__":
    Xmaster = np.array([[1, 0, 0],
                        [1, 1, 0],
                        [1, 2, 0],
                        [2, 9, 0],
                        [5, 3, 0],
                        ])
    offset = np.array([10, 20, 30])
    rotation_angles = np.array([0.003, -0.002, 0.0001, -1e-5])
    Xstage = XmtoXs(Xmaster, offset, rotation_angles)

    corr = [*offset, *rotation_angles]
    offset_2, rotation_angles_2 = solve_xyz(Xstage, Xmaster)
    corr2 = [*offset_2, *rotation_angles_2]
    print("XYZ corr",
          np.sqrt(np.mean(np.square(
                  XstoXm(Xstage, offset_2, rotation_angles_2) - Xmaster))),
          np.sqrt(np.mean(np.square(np.array([*corr]) - [*corr2]))))
    corr3 = solve_z(Xstage)

    print("Z corr", np.sqrt(
        np.mean(np.square(XstoXm(Xstage, corr3[0], corr3[1])[..., 2]))))


# class Zsolver():
#
#    def solve(self, Xstage):
#        """a*X + b*Y + c = Z
#        """
#        Xstage = np.asarray(Xstage)
#
#        N = len(Xstage)
#        if N == 0:
#            return np.zeros(3)
#
#        elif N < 3:
#            return np.array([0, 0, np.mean(Xstage[:, 2], 0)])
#
#        X, Y, Z = Xstage.T
#
#        M = np.asarray([[np.sum(X), np.sum(Y), len(X)],
#                        [np.sum(X * X), np.sum(X * Y), np.sum(X)],
#                        [np.sum(X * Y), np.sum(Y * Y), np.sum(Y)]])
#
#        b = np.asarray([[np.sum(Z)],
#                        [np.sum(X * Z)],
#                        [np.sum(Y * Z)]])
#
#        coeffs = np.linalg.inv(M)@b
#        return np.squeeze(coeffs)
#
#
# class XYsolver():
#
#    def solve(self, XYstage, XYmaster):
#        """ solve the rotation and translation of XYstage and XYmaster
#
#
#        with the least square method
#        returns the best guess for theta, origin
#
#        M@XYs = R@XYm + O
#        With M = [[1, sin], [0, cos]]
#        R rotation matrix
#        O offset
#        """
#
#        N = len(XYstage)
#        if N == 0:
#            return np.zeros(4)
#        elif N == 1:
#            return self.solve1(XYstage, XYmaster)
#        elif N == 2:
#            return self.solve2(XYstage, XYmaster)
#        else:
#            return self.solve3(XYstage, XYmaster)
#
#    def solve1(self, XYstage, XYmaster):
#        return np.asarray((0, 0, *np.squeeze(XYstage - XYmaster)))
#
#    def solve2(self, XYstage, XYmaster):
#
#        def getResidus(theta):
#            R = self.get_rotation_matrix(theta)
#            RXm = np.array([R@X for X in XYmaster])
#            origin = 1 / len(XYstage) * np.sum(XYstage - RXm, axis=0)
#            residus = np.sum((RXm + origin - XYstage)**2)
#            return origin, residus
#
#        # Get best theta
#        XYs2 = 1 / len(XYstage) * np.sum(XYstage, 0) - XYstage
#
#        dividend = np.sum(XYs2 * XYmaster)
#        divisor = np.sum(np.cross(XYs2, XYmaster))
#
#        if divisor == 0:
#            theta1 = 0
#        else:
#            theta1 = (np.arctan(dividend / divisor)
#                      - np.pi / 2)
#
#        # Theta is defined +-pi. Must test theta+pi
#        origin1, residus1 = getResidus(theta1)
#        theta2 = theta1 + np.pi
#        origin2, residus2 = getResidus(theta2)
#
#        # return best result
#        if residus1 < residus2:
#            return np.asarray([0, theta1, *origin1])
#        return np.asarray([0, theta2, *origin2])
#
#    def solve3(self, XYs, XYm):
#        XYs2 = XYs - 1 / len(XYs) * np.sum(XYs, 0)
#        XYm2 = XYm - 1 / len(XYm) * np.sum(XYm, 0)
#
#        YsXs2 = np.sum(XYs[:, 1] * XYs2[:, 0])
#        YsXm2 = np.sum(XYs[:, 1] * XYm2[:, 0])
#        YsYm2 = np.sum(XYs[:, 1] * XYm2[:, 1])
#        XmXs2 = np.sum(XYm[:, 0] * XYs2[:, 0])
#        YmXs2 = np.sum(XYm[:, 1] * XYs2[:, 0])
#        XmYs2 = np.sum(XYm[:, 0] * XYs2[:, 1])
#        YmYs2 = np.sum(XYm[:, 1] * XYs2[:, 1])
#
#        def fun(x, YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2):
#            theta, phi = x
#            return [np.cos(phi) * YsXs2
#                    - np.cos(theta + phi) * YsXm2
#                    + np.sin(theta + phi) * YsYm2,
#                    np.cos(theta + phi) * XmYs2
#                    - np.sin(theta + phi) * YmYs2
#                    - np.sin(theta) * XmXs2
#                    - np.cos(theta) * YmXs2]
#
#        def jac(x, YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2):
#            theta, phi = x
#            return [[np.sin(theta + phi) * YsXm2
#                     + np.cos(theta + phi) * YsYm2,
#                     - np.sin(phi) * YsXs2
#                     + np.sin(theta + phi) * YsXm2
#                     + np.cos(theta + phi) * YsYm2],
#                    [- np.sin(theta + phi) * XmYs2
#                     - np.cos(theta + phi) * YmYs2
#                     - np.cos(theta) * XmXs2
#                     + np.sin(theta) * YmXs2,
#                     - np.sin(theta + phi) * XmYs2
#                     - np.cos(theta + phi) * YmYs2]]
#
#        sol = optimize.root(fun, [0, 0], jac=jac, method='hybr',
#                       args=(YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2))
#        theta, phi = sol.x
#
#        Mphi = np.asarray([[1, np.sin(phi)],
#                           [0, np.cos(phi)]])
#        Rtheta = np.asarray([[np.cos(theta), -np.sin(theta)],
#                             [np.sin(theta), np.cos(theta)]])
#
#        Origin = 1 / len(XYs) * np.sum(np.asarray([Mphi@XY for XY in XYs])
#                                   - np.asarray([Rtheta@XY for XY in XYm]), 0)
#
#        return np.asarray([phi, theta, *Origin])
#
#    def get_rotation_matrix(self, theta):
#        c, s = np.cos(theta), np.sin(theta)
#        R = np.array([[c, -s], [s, c]])
#        return R
