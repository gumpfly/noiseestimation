from __future__ import print_function
import numpy as np
from scipy.linalg import block_diag
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from matplotlib import pyplot as plt
from noiseestimation.sensor import LinearSensor
from noiseestimation.correlator import Correlator
from noiseestimation.noiseestimator import estimate_noise, estimate_noise_approx


# parameters
sample_size = 200
used_taps = 100
measurement_var = 4


def setup():
    dt = 0.1
    # set up sensor sim
    F = np.array([[1, dt, 0,  0],
                  [0,  1, 0,  0],
                  [0,  0, 1, dt],
                  [0,  0, 0,  1]])
    H = np.array([[1, 0, 0, 0],
                  [0, 0, 1, 0]])
    x0 = np.array([[0],
                   [0.5],
                   [0],
                   [1]])
    sim = LinearSensor(x0, F, H)
    # set up kalman filter
    tracker = KalmanFilter(dim_x=4, dim_z=2)
    tracker.F = F
    q = Q_discrete_white_noise(dim=2, dt=dt, var=0.01)
    tracker.Q = block_diag(q, q)
    tracker.H = H
    tracker.R = np.diag([measurement_var, measurement_var])
    tracker.x = np.array([[0, 0, 0, 0]]).T
    tracker.P = np.eye(4) * 500
    return sim, tracker


def filtering(sim, tracker):
    # perform sensor simulation and filtering
    readings = []
    truths = []
    filtered = []
    residuals = []
    Rs = [np.eye(2) * measurement_var] * sample_size
    for R in Rs:
        sim.step()
        reading = sim.read(R)
        tracker.predict()
        tracker.update(reading)
        readings.append(reading)
        truths.append(sim.x)
        filtered.append(tracker.x)
        residuals.append(tracker.y)

    readings = np.asarray(readings)
    filtered = np.asarray(filtered)
    truths = np.asarray(truths)
    residuals = np.asarray(residuals)
    return readings, truths, filtered, residuals


def plot_results(readings, mu, error):
    # plot results
    f, axarr = plt.subplots(2)
    axarr[0].plot(readings[:, 0], readings[:, 1], 'go', label="Measurements")
    axarr[0].plot(mu[:, 0], mu[:, 1], 'm', linewidth=3, label="Filter")
    axarr[0].legend(loc="lower right")
    # axarr[0].set_xlim([0,200])
    axarr[0].set_title("Kalman filtering of position")

    axarr[1].plot(error, 'r')
    axarr[1].set_title("Estimation error")

    plt.show()


def perform_estimation(residuals, tracker, lags):
    cor = Correlator(residuals)
    correlation = cor.autocorrelation(lags)
    R = estimate_noise(
        correlation, tracker.K, tracker.F, tracker.H)
    R_approx = estimate_noise_approx(
        correlation[0], tracker.H, tracker.P, "posterior")
    print("Estimation: ", R)
    print("Approximated estimation: ", R_approx)
    # TODO Error calculation
    # abs_err = measurement_std**2 - R
    # rel_err = abs_err / measurement_std**2
    # print "True: %.3f" % measurement_std**2
    # print "Filter: %.3f" % tracker.R
    # print "Estimated: %.3f" % R
    # print "Absolute error: %.3f" % abs_err
    # print "Relative error: %.3f %%" % (rel_err * 100)
    # print "-" * 15
    # return rel_err


def run_tracker():
    # set up sensor simulator
    sim, tracker = setup()
    readings, truths, filtered, residuals = filtering(sim, tracker)

    # plot_results(readings, mu, error)

    rel_err = perform_estimation(residuals, tracker, used_taps)
    return rel_err


if __name__ == "__main__":
    run_tracker()
    # sum = .0
    # runs = 100
    # for i in range(runs):
    #     print "%d / %d" % (i+1, runs)
    #     sum += fabs(run_tracker())

    # print "Avg relative error: %.3f %%" % (sum * 100 / runs)
