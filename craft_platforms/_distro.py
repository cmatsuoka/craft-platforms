# This file is part of craft-platforms.
#
# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Distribution related utilities."""

from __future__ import annotations

import contextlib
import dataclasses
import typing
from types import NotImplementedType

import distro
from typing_extensions import Self


@typing.runtime_checkable
class BaseName(typing.Protocol):
    """A protocol for any class that can be used as an OS base.

    This protocol exists as a backwards compatibility shim for the
    language used in craft-providers.
    """

    name: str
    version: str


def _get_version_tuple(version_str: str) -> tuple[int | str, ...]:
    """Convert a version string into a version tuple."""
    parts = typing.cast(list[str | int], version_str.split("."))
    # Try converting each part to an integer, leaving as a string if not doable.
    for idx, part in enumerate(parts):
        with contextlib.suppress(ValueError):
            parts[idx] = int(part)
    return tuple(parts)


def _get_version(base: DistroBase | BaseName | tuple[str, str]) -> str:
    """Get the version of a base."""
    if isinstance(base, DistroBase):
        return base.series
    if isinstance(base, BaseName):
        return base.version
    return base[1]


@dataclasses.dataclass(repr=True)
class DistroBase:
    """A linux distribution base."""

    distribution: str
    series: str

    def _ensure_bases_comparable(
        self,
        other: DistroBase | BaseName | tuple[str, str],
    ) -> None:
        """Ensure that these bases are comparable, raising an exception if not.

        :param other: Another distribution base.
        :raises: ValueError if the distribution bases are not comparable.
        """
        if isinstance(other, DistroBase):
            other_distro = other.distribution
        elif isinstance(other, BaseName):
            other_distro = other.name
        else:
            other_distro = other[0]
        if self.distribution != other_distro:
            raise ValueError(
                f"Different distributions ({self.distribution} and {other_distro}) do not have comparable versions.",
            )

    def __eq__(self, other: object, /) -> bool | NotImplementedType:
        if isinstance(other, DistroBase):
            return (
                self.distribution == other.distribution and self.series == other.series
            )
        if isinstance(other, BaseName):
            return self.distribution == other.name and self.series == other.version
        if isinstance(other, tuple):
            return bool(self.distribution == other[0] and self.series == other[1])
        return NotImplemented

    def __lt__(self, other: BaseName | tuple[str, str]) -> bool:
        self._ensure_bases_comparable(other)
        self_version_tuple = _get_version_tuple(self.series)
        other_version_tuple = _get_version_tuple(_get_version(other))
        return self_version_tuple < other_version_tuple

    def __le__(self, other: BaseName | tuple[str, str]) -> bool:
        self._ensure_bases_comparable(other)
        self_version_tuple = _get_version_tuple(self.series)
        other_version_tuple = _get_version_tuple(_get_version(other))
        return self_version_tuple <= other_version_tuple

    def __gt__(self, other: BaseName | tuple[str, str]) -> bool:
        self._ensure_bases_comparable(other)
        self_version_tuple = _get_version_tuple(self.series)
        other_version_tuple = _get_version_tuple(_get_version(other))
        return self_version_tuple > other_version_tuple

    def __ge__(self, other: BaseName | tuple[str, str]) -> bool:
        self._ensure_bases_comparable(other)
        self_version_tuple = _get_version_tuple(self.series)
        other_version_tuple = _get_version_tuple(_get_version(other))
        return self_version_tuple >= other_version_tuple

    @classmethod
    def from_str(cls, base_str: str) -> Self:
        """Parse a distribution string to a DistroBase.

        :param base_str: A distribution string (e.g. "ubuntu@24.04")
        :returns: A DistroBase of this string.
        :raises: ValueError if the string isn't of the appropriate format.
        """
        if base_str.count("@") != 1:
            raise ValueError(
                f"Invalid base string {base_str!r}. Format should be '<distribution>@<series>'",
            )
        distribution, _, series = base_str.partition("@")
        return cls(distribution, series)

    @classmethod
    def from_linux_distribution(cls, distribution: distro.LinuxDistribution) -> Self:
        """Convert a distro package's LinuxDistribution object to a DistroBase.

        :param distribution: A LinuxDistribution from the distro package.
        :returns: A matching DistroBase object.
        """
        return cls(distribution=distribution.id(), series=distribution.version())


def is_ubuntu_like(distribution: distro.LinuxDistribution | None = None) -> bool:
    """Determine whether the given distribution is Ubuntu or Ubuntu-like.

    :param distribution: Linux distribution info object, or None to use the host system.
    :returns: A boolean noting whether the given distribution is Ubuntu or Ubuntu-like.
    """
    if distribution is None:
        distribution = distro.LinuxDistribution()
    if distribution.id() == "ubuntu":
        return True
    distros_like = distribution.like().split()
    if "ubuntu" in distros_like:
        return True
    return False
