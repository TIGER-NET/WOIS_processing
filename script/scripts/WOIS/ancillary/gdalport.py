# Copyright (c) 2014, Vienna University of Technology (TU Wien), Department
# of Geodesy and Geoinformation (GEO).
# All rights reserved.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL VIENNA UNIVERSITY OF TECHNOLOGY,
# DEPARTMENT OF GEODESY AND GEOINFORMATION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author: Senmao Cao
# Creation date: 2013-12-16

# History
#-------------------------------------------
# Author:
# Date:
# Modification:
#--------------


"""A sample class and Some handy functions for using gdal library to read/write data."""


import subprocess
from osgeo import gdal
from osgeo import gdalconst
gdal.AllRegister()

class GdalImage:
    """A sample class to access a image with GDAL library"""

    def __init__(self, gdaldataset):
        self.dataset = gdaldataset

    def close(self):
        """close the dataset"""
        self.dataset = None

    def read_band(self, band_idx, subset=None):
        """Read data from given band.

        Parameters
        ----------
        band_idx : int
            The band index starting from 1.
        subset : list or tuple
            The subset should be in pixles, like this (xmin, ymin, xmax, ymax).

        Returns
        ------
        2darray
            the 2d array including data reading from given band

        """
        if band_idx < 1 or band_idx > self.dataset.RasterCount:
            raise IndexError("band index is out of range")
        band = self.dataset.GetRasterBand(band_idx)
        if subset is None:
            data = band.ReadAsArray(0, 0, band.XSize, band.YSize)
        else:
            data = band.ReadAsArray(subset[0], subset[1], subset[2], subset[3])
        return data

    def XSize(self):
        """get the width of the image"""
        return self.dataset.RasterXSize if self.dataset else None

    def YSize(self):
        """get the height of the image"""
        return self.dataset.RasterYSize if self.dataset else None

    def get_raster_nodata_value(self, band_idx=1):
        """get the nodatave.

        Parameters
        ----------
        band_idx : int
            the band index

        Returns
        -------
        nodata
            no data value if it's available, otherwise it will return None

        """
        if band_idx < 1 or band_idx > self.dataset.RasterCount:
            raise IndexError("band index is out of range")
        return self.dataset.GetRasterBand(band_idx).GetNoDataValue()

    def read_all_band(self):
        """read the data of all the bands"""
        raise NotImplementedError("sorry, read_all_band has not been implemented!")

    def get_raster_dtype(self, band_idx=1):
        """get the data type of given band"""
        if band_idx < 1 or band_idx > self.dataset.RasterCount:
            raise IndexError("band index is out of range")
        return self.dataset.GetRasterBand(band_idx).DataType

    def geotransform(self):
        """get the geotransform data"""
        return self.dataset and self.dataset.GetGeoTransform() or None

    def projection(self):
        """get the projection string in wkt format"""
        return self.dataset and self.dataset.GetProjection() or None

    def band_count(self):
        """get the band count"""
        return self.dataset and self.dataset.RasterCount or None

    def get_extent(self):
        """get the extent of the image as (xmin, ymin, xmax, ymax)."""
        geot = self.geotransform()
        return (geot[0], geot[3] + self.YSize() * geot[5],
                geot[0] + self.XSize() * geot[1], geot[3])


def open_image(filename):
    """ open an image file

    Parameters
    ----------
    filename : string. full path string of input file

    Returns
    -------
    GdalImage
        GdalImage object if successful, otherwise None

    Raise
    ------
    IOError
        if fail to open the image file

    """

    dataset = gdal.Open(filename, gdalconst.GA_ReadOnly)
    if dataset is None:
        raise IOError("cannot open %s" % filename)

    return GdalImage(dataset)


def get_gdal_datatype(datatype):
    """get gdal data type from datatype

    Parameters
    ----------
    datatype :  string.
            data type string in python such as "uint8", "float32" and so forth.

    Returns
    -------
    gdal_datatype
            gdal data type
    """
    gdal_datatype = gdalconst.GDT_Unknown
    datatype = datatype.lower()
    if datatype == 'uint8':
        gdal_datatype = gdalconst.GDT_Byte
    elif datatype == 'int16':
        gdal_datatype = gdalconst.GDT_Int16
    elif datatype == 'int32':
        gdal_datatype = gdalconst.GDT_Int32
    elif datatype == 'uint16':
        gdal_datatype = gdalconst.GDT_UInt16
    elif datatype == 'uint32':
        gdal_datatype = gdalconst.GDT_UInt32
    elif datatype == 'float32':
        gdal_datatype = gdalconst.GDT_Float32
    elif datatype == 'float64':
        gdal_datatype = gdalconst.GDT_Float64
    elif datatype == 'complex64':
        gdal_datatype = gdalconst.GDT_CFloat32
    elif datatype == 'complex128':
        gdal_datatype = gdalconst.GDT_CFloat64
    return gdal_datatype


def get_gdal_resampling_type(resampling_method):
    """get gdal resample type from resampling method string"""
    gdal_RA = None
    resampling_method = resampling_method.lower()
    if resampling_method == 'nearest':
        gdal_RA = gdal.GRA_NearestNeighbour
    elif resampling_method == 'bilinear':
        gdal_RA = gdal.GRA_Bilinear
    elif resampling_method == 'cubic':
        gdal_RA = gdal.GRA_Cubic
    elif resampling_method == 'cubicspline':
        gdal_RA = gdal.GRA_CubicSpline
    elif resampling_method == 'lanczos':
        gdal_RA = gdal.GRA_Lanczos

    return gdal_RA


def create_dataset(filename, datatype, dims, frmt="GTiff", geotransform=None, projection=None, option=None):
    """create GDAL dataset.

    Parameters
    ----------
    filename : string
        full path of output filename.
    datatype : string
        data type string like numpy's dtpye.
    dims : tuple
        Dimension of the dataset in the format of (bands, XSize, YSize)
    frmt :  string
        The format of output image should be a string that gdal supported.
    geotransform : array like
        It contains six geotransform parameters.
    projection : string
        projection definition string.

    Returns
    -------
    GDAL dataset

    Raise:
    ------
    IOError
        if fail to obtain driver with specific format or to create the output dataset

    """
    driver = gdal.GetDriverByName(frmt)
    gdaldatatype = get_gdal_datatype(datatype)
    if driver is None:
        raise IOError("cannot get driver of {}".format(frmt))
    band_count, xsize, ysize = dims
    if option is None:
        out_ds = driver.Create(filename, xsize, ysize, band_count, gdaldatatype)
    else:
        out_ds = driver.Create(filename, xsize, ysize, band_count,
                               gdaldatatype, option)
    if out_ds is None:
        raise IOError("cannot create file of {}".format(filename))
    if not geotransform is None:
        out_ds.SetGeoTransform(geotransform)
    if not projection is None:
        out_ds.SetProjection(projection)
    return out_ds


def write_image(image, filename, frmt="GTiff", nodata=None,
                geotransform=None, projection=None, option=None):
    """output image into filename with specific format

    Parameters
    ----------
    image : array like
        two dimension array containing data that will be stored
    filename : string
        full path of output filename
    frmt :  string
        the format of output image should be a string that gdal supported.
    nodata : list, optional
        a list contian the nodata values of each band
    geotransform : array like
        contain six geotransform parameters
    projection : string
        projection definition string

    Returns
    -------
    dataset
        the gdal dataset object of output dataset

    Raise
    -----
        IOError
            if IO error happens
        ValueError
            if some invalid parameters are given

    """
    # to make sure dim of image is 2 or 3
    if image is None or image.ndim < 2 or image.ndim > 3:
        raise ValueError(
            "The image is None or it's dimension isn't in two or three.")
    dims = (1, image.shape[1], image.shape[0]) if image.ndim == 2 \
        else (image.shape[2], image.shape[1], image.shape[0])
    # create dataset
    ds = create_dataset(filename, str(image.dtype), dims, frmt, geotransform, projection, option)
    # write data
    if image.ndim == 2:
        ds.GetRasterBand(1).WriteArray(image, 0, 0)
    else:
        for i in xrange(ds.RasterCount):
            ds.GetRasterBand(i + 1).WriteArray(image[:, :, i], 0, 0)

    if nodata is not None:
        for i in xrange(ds.RasterCount):
            ds.GetRasterBand(i + 1).SetNoDataValue(nodata[i])

    return ds


def call_gdalwarp(srcfiles, dstfile, gdalwarp_path=None, **kwargs):
    """call the gdalwarp executable and check its result."""
    cmd = []
    if gdalwarp_path:
        cmd.append(os.path.join(gdalwarp_path, "gdalwarp"))
    else:
        cmd.append("gdalwarp")
    for k, v in kwargs.iteritems():
        cmd.append("-{} {}".format(k, v))
    # using quations with filepath in case of including spaces in the path
    srcfiles = ['\"{}\"'.format(x) for x in srcfiles]
    cmd.extend(srcfiles)
    cmd.append('\"{}\"'.format(dstfile))
    if gdalwarp_path:
        output = subprocess.check_output(" ".join(cmd), shell=True, cwd=gdalwarp_path)
    else:
        output = subprocess.check_output(" ".join(cmd), shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    successed = True if output.find("100 - done.") > 0 else False
    #print output
    return (successed, output)
