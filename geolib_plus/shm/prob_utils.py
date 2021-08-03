
# import packages

from typing import Iterable
from pydantic import BaseModel

import numpy as np
from scipy.stats import t
from scipy.stats import norm


class ProbUtils(BaseModel):

    @staticmethod
    def calculate_student_t_factor(ndof: int, quantile: float) -> float:
        """
        Gets student t factor from student t distribution

        :param ndof: number of degrees of freedom
        :param quantile: quantile where the student t factor should be calculated
        :return: Student t factor
        """

        return t(ndof).ppf(quantile)

    @staticmethod
    def correct_std_with_student_t(ndof: int, quantile: float, std: float, a: float = 0) -> float:
        """
        Calculates corrected standard deviation at a quantile with the student-t factor. This includes an optional
        spread reduction factor.

        :param ndof: number of degrees of freedom
        :param quantile: quantile where the student t factor should be calculated
        :param std: standard deviation
        :param a: spread reduction factor, 0.75 for regional sample collection; 1.0 for local sample collection
        :return: corrected standard deviation
        """

        # get student t factor
        t_factor = ProbUtils.calculate_student_t_factor(ndof-1, quantile)

        # get value at percentile for normal distribution
        norm_factor = norm.ppf(quantile)

        # calculate corrected standard deviation
        corrected_std = t_factor/norm_factor * std * np.sqrt((1-a) + (1/ndof))

        return corrected_std

    @staticmethod
    def calculate_prob_parameters_from_lognormal(data: Iterable, is_local: bool, quantile=0.05):
        """
        Calculates probabilistic parameters mu and sigma from a lognormal dataset, as required in D-stability. This
        function takes into account spread reduction factor and the student t factor

        :param data: dataset, X
        :param is_local: true if data collection is local, false if data collection is regional
        :param quantile: quantile where the student t factor should be calculated
        """
        log_mean, log_std = ProbUtils.calculate_log_stats(data)

        # set spread reduction factor, 0.75 if data collection is regional, 1.0 if data collection is local
        if is_local:
            a = 1
        else:
            a = 0.75

        corrected_std = ProbUtils.correct_std_with_student_t(len(data), quantile, log_std, a)

        mean_prob, std_prob = ProbUtils.get_mean_std_from_lognormal(log_mean, corrected_std)

        return mean_prob, std_prob


    @staticmethod
    def get_mean_std_from_lognormal(log_mean: float, log_std: float):
        """
        Calculates normal mean and standard deviation from the mean and std of LN(X)

        :param log_mean: mean of LN(X)
        :param log_std: std of LN(X)
        :return: mean and std of X
        """

        mean = np.exp(log_mean + (log_std**2)/2)
        std = mean * np.sqrt(np.exp(log_std ** 2) - 1)

        return mean, std

    @staticmethod
    def get_log_mean_std_from_normal(mean, std):
        """
        Calculates mean and standard deviation of LN(X) from the mean and std of X

        :param mean: mean of X
        :param std: std X
        :return: mean and std of LN(X)
        """

        log_mean = np.log(mean ** 2 / (np.sqrt(std ** 2 + mean ** 2)))
        log_std = np.sqrt(np.log((std/mean)**2 + 1))

        return log_mean, log_std

    @staticmethod
    def calculate_log_stats(data: Iterable):
        """
        Calculates mean and std of LN(X)

        :param data: dataset, X
        :return: mean and std of LN(X)
        """
        log_mean = np.sum(np.log(data)) / len(data)
        log_std = np.sqrt(np.sum((np.log(data)-log_mean)**2) / (len(data) - 1))

        return log_mean, log_std

    @staticmethod
    def calculate_normal_stats(data: Iterable):
        """
        Calculates mean and std of X

        :param data: dataset, X
        :return: mean and std of X
        """
        mean = np.sum(data) / len(data)
        std = np.sqrt(np.sum((data - mean)**2) / (len(data) - 1))

        return mean, std

    @staticmethod
    def calculate_characteristic_value_from_dataset(data: Iterable, is_local: bool, is_low: bool,
                                                    is_log_normal: bool = True, char_quantile: float = 0.05):
        """
        Calculates the characteristic value of the dataset. A normal distribution or a lognormal distribution can be
        assumed for the dataset. The student-t distribution is taken into account. And the spread reduction factor is
        taken into account

        :param data: dataset, X
        :param is_local: true if data collection is local, false if data collection is regional
        :param is_low: true if low characteristic value is to be calculated, false if high characteristic value desired
        :param is_log_normal: True if a log normal distribution is assumed, false for normal distribution
        :param char_quantile: Quantile which is considered for the characteristic value

        :return: characteristic value of the dataset
        """

        direction_factor = -1 if is_low else 1

        # set spread reduction factor, 0.75 if data collection is regional, 1.0 if data collection is local
        if is_local:
            a = 1
        else:
            a = 0.75

        if is_log_normal:
            # calculate characteristic value from log normal distribution
            log_mean, log_std = ProbUtils.calculate_log_stats(data)

            # correct std for spread and amount of tests
            estimated_std = abs(ProbUtils.calculate_student_t_factor(len(data)-1,char_quantile) * \
                            log_std * np.sqrt((1-a) + 1/len(data)))

            x_kar = np.exp(log_mean + direction_factor*estimated_std)
        else:
            # calculate characteristic value from normal distribution
            mean, std = ProbUtils.calculate_normal_stats(data)

            # correct std for spread and amount of tests
            estimated_std = abs(ProbUtils.calculate_student_t_factor(len(data) - 1, char_quantile) * \
                                std * np.sqrt((1 - a) + 1 / len(data)))

            x_kar = mean + direction_factor * estimated_std

        return x_kar


