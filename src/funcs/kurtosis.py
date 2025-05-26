from numba import njit, prange  # type: ignore
import numpy as np
from numpy.typing import NDArray

@njit(cache=True) # type: ignore
def compute_kurtosis(
    observation_count: int,
    sum_values: float,
    sum_values_squared: float,
    sum_values_cubed: float,
    sum_values_fourth: float,
    consecutive_equal_count: int,
    min_length: int = 4,
) -> float | np.float32:
    if observation_count >= min_length:
        if observation_count < 4:
            return np.nan
        elif consecutive_equal_count >= observation_count:
            return -3.0
        else:
            total_observations = float(observation_count)
            mean: float = sum_values / total_observations
            variance: float = sum_values_squared / total_observations - mean * mean
            skewness_term: float = (
                sum_values_cubed / total_observations
                - mean * mean * mean
                - 3 * mean * variance
            )
            kurtosis_term: float = (
                sum_values_fourth / total_observations
                - mean * mean * mean * mean
                - 6 * variance * mean * mean
                - 4 * skewness_term * mean
            )

            if variance <= 1e-14:
                return np.nan
            else:
                kurtosis: float = (
                    total_observations * total_observations - 1.0
                ) * kurtosis_term / (variance * variance) - 3.0 * (
                    (total_observations - 1.0) ** 2
                )
                return kurtosis / (
                    (total_observations - 2.0) * (total_observations - 3.0)
                )
    else:
        return np.nan


@njit(cache=True) # type: ignore
def add_kurtosis_contribution(
    value: float,
    observation_count: int,
    sum_values: float,
    sum_values_squared: float,
    sum_values_cubed: float,
    sum_values_fourth: float,
    compensation_values: float,
    compensation_squared: float,
    compensation_cubed: float,
    compensation_fourth: float,
    consecutive_equal_count: int,
    previous_value: float,
) -> tuple[int, float, float, float, float, float, float, float, float, int, float]:
    if value == value:
        observation_count += 1

        temp: float = value - compensation_values
        total: float = sum_values + temp
        compensation_values = total - sum_values - temp
        sum_values = total

        temp = value * value - compensation_squared
        total = sum_values_squared + temp
        compensation_squared = total - sum_values_squared - temp
        sum_values_squared = total

        temp = value * value * value - compensation_cubed
        total = sum_values_cubed + temp
        compensation_cubed = total - sum_values_cubed - temp
        sum_values_cubed = total

        temp = value * value * value * value - compensation_fourth
        total = sum_values_fourth + temp
        compensation_fourth = total - sum_values_fourth - temp
        sum_values_fourth = total

        if value == previous_value:
            consecutive_equal_count += 1
        else:
            consecutive_equal_count = 1
        previous_value = value

    return (
        observation_count,
        sum_values,
        sum_values_squared,
        sum_values_cubed,
        sum_values_fourth,
        compensation_values,
        compensation_squared,
        compensation_cubed,
        compensation_fourth,
        consecutive_equal_count,
        previous_value,
    )


@njit(cache=True) # type: ignore
def remove_kurtosis_contribution(
    value: float,
    observation_count: int,
    sum_values: float,
    sum_values_squared: float,
    sum_values_cubed: float,
    sum_values_fourth: float,
    compensation_values: float,
    compensation_squared: float,
    compensation_cubed: float,
    compensation_fourth: float,
) -> tuple[int, float, float, float, float, float, float, float, float]:
    if value == value:
        observation_count -= 1

        temp: float = -value - compensation_values
        total: float = sum_values + temp
        compensation_values = total - sum_values - temp
        sum_values = total

        temp = -value * value - compensation_squared
        total = sum_values_squared + temp
        compensation_squared = total - sum_values_squared - temp
        sum_values_squared = total

        temp = -value * value * value - compensation_cubed
        total = sum_values_cubed + temp
        compensation_cubed = total - sum_values_cubed - temp
        sum_values_cubed = total

        temp = -value * value * value * value - compensation_fourth
        total = sum_values_fourth + temp
        compensation_fourth = total - sum_values_fourth - temp
        sum_values_fourth = total

    return (
        observation_count,
        sum_values,
        sum_values_squared,
        sum_values_cubed,
        sum_values_fourth,
        compensation_values,
        compensation_squared,
        compensation_cubed,
        compensation_fourth,
    )


@njit(cache=True) # type: ignore
def get_kurtosis(array: NDArray[np.float32], length: int, min_length: int) -> NDArray[np.float32]:
    num_rows, num_cols = array.shape
    output = np.full(shape=(num_rows, num_cols), fill_value=np.nan, dtype=np.float32)

    for col in prange(num_cols):
        (
            observation_count,
            sum_values,
            sum_values_squared,
            sum_values_cubed,
            sum_values_fourth,
        ) = 0, 0.0, 0.0, 0.0, 0.0
        (
            compensation_values,
            compensation_squared,
            compensation_cubed,
            compensation_fourth,
        ) = 0.0, 0.0, 0.0, 0.0
        previous_value = array[0, col]
        consecutive_equal_count = 0

        for row in range(num_rows):
            start_idx: int = max(0, row - length + 1)
            end_idx: int = row + 1

            if row == 0 or start_idx >= row - 1:
                (
                    observation_count,
                    sum_values,
                    sum_values_squared,
                    sum_values_cubed,
                    sum_values_fourth,
                ) = 0, 0.0, 0.0, 0.0, 0.0
                (
                    compensation_values,
                    compensation_squared,
                    compensation_cubed,
                    compensation_fourth,
                ) = 0.0, 0.0, 0.0, 0.0
                previous_value = array[start_idx, col]
                consecutive_equal_count = 0
                for idx in range(start_idx, end_idx):
                    (
                        observation_count,
                        sum_values,
                        sum_values_squared,
                        sum_values_cubed,
                        sum_values_fourth,
                        compensation_values,
                        compensation_squared,
                        compensation_cubed,
                        compensation_fourth,
                        consecutive_equal_count,
                        previous_value,
                    ) = add_kurtosis_contribution(
                        value=array[idx, col],
                        observation_count=observation_count,
                        sum_values=sum_values,
                        sum_values_squared=sum_values_squared,
                        sum_values_cubed=sum_values_cubed,
                        sum_values_fourth=sum_values_fourth,
                        compensation_values=compensation_values,
                        compensation_squared=compensation_squared,
                        compensation_cubed=compensation_cubed,
                        compensation_fourth=compensation_fourth,
                        consecutive_equal_count=consecutive_equal_count,
                        previous_value=previous_value,
                    )
            else:
                for idx in range(max(0, row - length), start_idx):
                    (
                        observation_count,
                        sum_values,
                        sum_values_squared,
                        sum_values_cubed,
                        sum_values_fourth,
                        compensation_values,
                        compensation_squared,
                        compensation_cubed,
                        compensation_fourth,
                    ) = remove_kurtosis_contribution(
                        value=array[idx, col],
                        observation_count=observation_count,
                        sum_values=sum_values,
                        sum_values_squared=sum_values_squared,
                        sum_values_cubed=sum_values_cubed,
                        sum_values_fourth=sum_values_fourth,
                        compensation_values=compensation_values,
                        compensation_squared=compensation_squared,
                        compensation_cubed=compensation_cubed,
                        compensation_fourth=compensation_fourth,
                    )

                (
                    observation_count,
                    sum_values,
                    sum_values_squared,
                    sum_values_cubed,
                    sum_values_fourth,
                    compensation_values,
                    compensation_squared,
                    compensation_cubed,
                    compensation_fourth,
                    consecutive_equal_count,
                    previous_value,
                ) = add_kurtosis_contribution(
                    value=array[row, col],
                    observation_count=observation_count,
                    sum_values=sum_values,
                    sum_values_squared=sum_values_squared,
                    sum_values_cubed=sum_values_cubed,
                    sum_values_fourth=sum_values_fourth,
                    compensation_values=compensation_values,
                    compensation_squared=compensation_squared,
                    compensation_cubed=compensation_cubed,
                    compensation_fourth=compensation_fourth,
                    consecutive_equal_count=consecutive_equal_count,
                    previous_value=previous_value,
                )

            output[row, col] = compute_kurtosis(
                observation_count=observation_count,
                sum_values=sum_values,
                sum_values_squared=sum_values_squared,
                sum_values_cubed=sum_values_cubed,
                sum_values_fourth=sum_values_fourth,
                consecutive_equal_count=consecutive_equal_count,
                min_length=min_length,
            )

    return output
