#!/usr/bin/env python

import six
import numpy as np
import pandas as pd

from amen.time import TimeSlice

class Feature(object):
    """
    Core feature container object.  Handles indexing and time-slicing.

    Attributes
    ---------

    Methods
    ------
    at(time_slices)
        Resample the feature at the given TimeSlices
    """
    def __init__(self, data, aggregate=np.mean, base=None):
        """
        Constructor for feature object

        Parameters
        ----------
        data: pandas.DataFrame
            Time-indexed data frame of features

        aggregate: function
            resample-aggregation function or mapping

        Returns
        ------
        A Feature object
        """

        # Check that the arguments have the right types
        assert isinstance(data, pd.DataFrame)

        self.data = data
        self.aggregate = aggregate
        # Not sure that this is the right way to do it - I feel like we're outsmarting pandas
        # pandas supports multiple keys in a dataframe.
        # Should we replace featurecollection with something like that?
        self.name = data.keys()[0]

        if base is not None:
            print type(base)
            print base
            print base.data, base.aggregate, base.base, base.name
            print isinstance(base, Feature)
            print isinstance(base, TimeSlice)
            assert isinstance(base, Feature)

        self.base = base

    def __iter__(self):
        """
        Wrapper to allow easy access to the internal data of the pandas dataframe
        """
        for d in self.data[self.name]:
            yield d
        
    def __repr__(self):
        args =(self.name)
        return '<Feature, {0}>'.format(args)
        
    def at(self, time_slices):
        """
        Resample the data at a new time slice index.

        Parameters
        ----------
        time_slices: TimeSlice or TimeSlice collection
            The time slices at which to index this feature object

        Returns
        -------
        Feature
            The resampled feature data
        """

        if self.base is not None:
            return self.base.at(time_slices)

        if isinstance(time_slices, TimeSlice):
            time_slices = [time_slices]

        # join the time slice values
        timed_data = pd.DataFrame(columns=self.data.columns)

        # make the new data
        for sl in time_slices:
            slice_index = ((sl.time <= self.data.index) &
                           (self.data.index < sl.time + sl.duration))
            timed_data.loc[sl.time] = self.aggregate(self.data[slice_index], axis=0)

        # return the new feature object
        return Feature(data=timed_data, aggregate=self.aggregate, base=self)


class FeatureCollection(dict):
    """
    A dictionary of features.

    Delegates `.at` to the features it contains.

    Allows for selection of multiple keys, which returns a smaller feature collection.
    """

    def at(self, time_slices):
        """
        Resample each feature at a new time slice index.

        Parameters
        ----------
        time_slices : TimeSlice or TimeSlice collection
            The time slices at which to index this feature object

        Returns
        -------
        new_features : FeatureCollection
            The resampled feature data
        """
        new_features = FeatureCollection()
        for key in self.keys():
            new_features[key] = self[key].at(time_slices)
        return new_features

    def get(self, keys):
        """
        Get a subset of the keys in the currect feature collection

        Parameters
        ----------
        keys : A string or list of strings
            The keys to return from the current feature collection

        Returns
        -------
        new_features : FeatureCollection
            The subset of keys
        """
        if type(keys) != list:
            keys = [keys]

        new_features = FeatureCollection()
        for key in keys:
            if key in self:
                new_features[key] = self[key]
        return new_features

