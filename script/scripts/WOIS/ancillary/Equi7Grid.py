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
# E-mail: Senmao.Cao@geo.tuwien.ac.at
# Creation date: 2014-07-17
# 2014-10-01 upgrade to equi7 version 1.1


""" Equi7 Grid System """


import os
import sys
from osgeo import ogr, osr, gdal
import gdalport
# from general import root_path as root

# !!!Attention:
# Geos support of Gdal library should be enable for the accurate spatial operation,
# otherwise, the search overlapped tiles will not be completely accurate.
# And it also depends the grids' zone shape files of bothe aeqd and wgs84.

ogr.RegisterAll()

class Equi7Grid(object):
    """Equi7 Grid.

    Methods
    -------
    get_projection(grid)
        return the projection of the given grid.
    get_grid_zone(grid)
        return an ogr geometry of the grid zone.
    get_grid_zone_wgs84(grid)
        return an ogr geometry of the grid zone in wgs84 project.
    identify_grid(area)
        Find overlapping grids with the area.
    identfy_tile(grid, location, res=0)
        return the name of the tile covering the location.
    create_dummy_dataset(tile, filename, datatype, frmt="GTiff", options=None)
        create a dataset with the correct geo information.
    search_tiles(area, area_proj=None, grids=None, res=0)
        find overlapping tile of the given area.
    resample(image, res, output_dir, outshortname=None, compress=True, resampling_type="bilinear", tile_nodata=None)
        resample image to tiles.
    """
    def __init__(self):
        """ construct grid system.

        Parameters
        ----------
        grid_id : string
            grid_id should be a string like AF075. The first two chars specify the continent
            while the last three digits give the resolution.
        """
        #self.grids = ["NA", "EU", "AS", "SA", "AF", "OC", "AN"]
        self.grids = ["AF"]
        self.tile_xspan = 600000  # tile span is fixed.
        self.tile_yspan = 600000
        self.__grid_zones_aeqd = None
        self.__grid_zones_wgs84 = None

    def __get_equi7_path(self):
        equi7_path = os.path.dirname(__file__)
        if not equi7_path or not os.path.exists(equi7_path):
            raise RuntimeError("Can not find the valid Equi7 grid path!")
        return equi7_path

    def __get_shapefile_path(self, grid):
        middle_folder = {"NA": "northamerica", "EU": "europe", "AS": "asia",
                         "SA": "southamerica", "AF": "africa", "OC": "oceania", "AN": "antarctica"}
        return os.path.join(self.__get_equi7_path(), middle_folder[grid])

    def __get_zone_name(self, grid):
        shapenames = {"NA": "equi7_northamerica_zone", "EU": "equi7_europe_zone", "AS": "equi7_asia_zone",
                     "SA": "equi7_southamerica_zone", "AF": "equi7_africa_zone", "OC": "equi7_oceania_zone",
                     "AN": "equi7_antarctica_zone"}
        return shapenames[grid]

    def __load_grid_zones_aeqd(self):
        """load the grid zone shapfile"""
        if self.__grid_zones_aeqd:
            return False
        self.__grid_zones_aeqd = dict()
        for grid in self.grids:
            # reading data
            fname = os.path.join(self.__get_shapefile_path(grid), "aeqd",
                                 "".join((self.__get_zone_name(grid) + "_aeqd.shp")))
            driver = ogr.GetDriverByName('ESRI Shapefile')
            dataSource = driver.Open(fname, 0)  # 0 means read-only. 1 means writeable.
            if dataSource is None:
                print 'Could not open the zone shape file: %s' % (fname)
            else:
                # only a feature in this shapefile
                # clone the feature's geometry
                f = dataSource.GetLayer().GetNextFeature()
                geom = f.GetGeometryRef().Clone()
                # transform
                self.__grid_zones_aeqd[grid] = geom
                dataSource.Destroy()
        return True

    def __load_grid_zones_wgs84(self):
        """load the grid zone of wgs84 projection."""
        if self.__grid_zones_wgs84:
            return False
        self.__grid_zones_wgs84 = dict()
        for grid in self.grids:
            # reading data
            fname = os.path.join(self.__get_shapefile_path(grid), "wgs84",
                                 "".join((self.__get_zone_name(grid) + "_wgs84.shp")))
            driver = ogr.GetDriverByName('ESRI Shapefile')
            dataSource = driver.Open(fname, 0)  # 0 means read-only. 1 means writeable.
            if dataSource is None:
                print 'Could not open the zone shape file of latlon project: %s' % (fname)
            else:
                multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
                for feature in dataSource.GetLayer():
                    multipolygon.AddGeometry(feature.GetGeometryRef())
                self.__grid_zones_wgs84[grid] = multipolygon
                dataSource.Destroy()
        return True

    def get_grid_zone_aeqd(self, grid):
        """return an geometry object which represents the zone of the given
        grid system in azimuthal equi distance projection.
        """
        zone = None
        try:
            zone = self.__grid_zones_aeqd[grid]
        except:
            self.__grid_zones_aeqd = None
            self.__load_grid_zones_aeqd()
            zone = self.__grid_zones_aeqd[grid]
        return zone

    def get_grid_zone_wgs84(self, grid):
        """return an geometry object which represents the zone of the given
        grid system in lat/lon projection.
        """
        zone = None
        try:
            zone = self.grid_geo_zones[grid]
        except:
            self.__grid_zones_wgs84 = None
            self.__load_grid_zones_wgs84()
            zone = self.__grid_zones_wgs84[grid]
        return zone

    def get_projection(self, grid):
        """return the projection of the given grid system in wkt formation"""
        zone = self.get_grid_zone_aeqd(grid)
        return zone.GetSpatialReference().ExportToWkt()

    def _create_polygon(self, area):
        """create a polygon geometry from area."""
        edge = ogr.Geometry(ogr.wkbLinearRing)
        [edge.AddPoint(x, y) for x, y in area]
        edge.CloseRings()
        geom_area = ogr.Geometry(ogr.wkbPolygon)
        geom_area.AddGeometry(edge)
        return geom_area

    def identify_grid(self, area):
        """return the overlapped grid ids."""
        geom_area= self._create_polygon(area)
        return [grid for grid in self.grids if geom_area.Intersects(self.get_grid_zone_wgs84(grid))]

    def identfy_tile(self, grid, location, res=None):
        """Return the tile name."""
        east = (int(location[0]) / self.tile_xspan) * self.tile_xspan / 100000
        north = (int(location[1]) / self.tile_yspan) * self.tile_yspan / 100000
        res = 0 if res is None else int(res)
        return "{}{:03d}_E{:03d}N{:03d}".format(grid, res, east, north)

    def get_tile_extent(self, tile):
        """return the extent of the tile in the terms of [minX,minY,maxX,maxY]."""
        east = int(tile[7:10]) * 100000
        north = int(tile[11:]) * 100000
        return [east, north, east + self.tile_xspan, north + self.tile_yspan]

    def create_dummy_dataset(self, tile, filename, datatype, frmt="GTiff", options=None):
        """create a gdal dataset object for the given tile."""
        # get info from tile name
        grid_id = tile[0:2]
        res = int(tile[2:5])
        east = int(tile[7:10])
        north = int(tile[11:])
        # create dataset
        dims = (1, int(self.tile_xspan / res), int(self.tile_yspan / res))
        geot = [east * 100000, res, 0,
                north * 100000 + self.tile_yspan, 0, -res]
#         if options is None:
#             options = ["COMPRESS=LZW"]
        return gdalport.create_dataset(filename, datatype, dims,
                                       frmt, geotransform=geot,
                                       projection=self.get_projection(grid_id),
                                       option=options)

    def search_tiles(self, area, area_proj=None, grids=None, res=0):
        """
        Search the tiles which are intersected by the poly_roi area.

        Parameters
        ----------
        area : list
            It is a polygon representing the region of interest.
            The polygon is list of tuples to represent a sample polygon.
            Each tuple in the list is a point of (x, y) or (lon, lat).
        area_proj : wkt string
            It is the projection information about the area polygon. Default value is None which
            means the lat/lon projection of WGS84

        grid : string
            grid ID to specified which continent you want to search. Default value is
            None for searching all continents.

        res : int
            The resolution of tiles in the grid system. Default is 0 for unknown resolution.
            It will use 000 to specify the resolution in the tile name.

        Returns
        -------
        list
            return a list of  the overlapped tiles' name. If not found, return empty list.
        """
        # check input grids
        if grids is None:
            grids = self.grids
        elif set(grids).issubset(set(self.grids)):
            grids = list(grids)
        else:
            raise ValueError("Invalid agrument: grid must one of [ %s ]." % " ".join(self.grids))

        # if projection is not in lon/lat projection
        geo_sr = osr.SpatialReference()
        geo_sr.SetWellKnownGeogCS("EPSG:4326")
        if area_proj:
            area_sr = osr.SpatialReference()
            area_sr.ImportFromWkt(area_proj)
            if not geo_sr.IsSame(area_sr):
                tx = osr.CoordinateTransformation(area_sr, geo_sr)
                prj_area = []
                for x, y in area:
                    (tr_x, tr_y, _) = tx.TransformPoint(x, y)
                    prj_area.append((tr_x, tr_y))
                area = prj_area

        # intersect the given grid ids and the overlapped ids
        #overlapped_grids = self.identify_grid(area)
        #grids =#list(set(grids) & set(overlapped_grids))
        grids = ["AF"]
        
        # create geometry
        geom_area = self._create_polygon(area)
        geom_area.AssignSpatialReference(geo_sr)

        # finding tiles
        overlapped_tiles = list()
        for grid in grids:
            overlapped_tiles.extend(self.__search_grid_tiles(geom_area, grid, res))
        return overlapped_tiles

    def __search_grid_tiles(self, area_geometry, grid, res=0):
        """
        Search the tiles which are overlapping with the given area.

        Parameters
        ----------
        area : list
            It is a polygon representing the region of interest.
            The polygon is list of tuples to represent a sample polygon.
            Each tuple in the list is a point of (x, y) or (lon, lat).
        grid : string
            grid ID to specified which continent you want to search. Default value is
            None for searching all continents.
        area_proj : wkt string
            It is the projection information about the area polygon.
        res : int
            The resolution of tiles in the grid system. Default is None for unknown resolution.
            It will use 000 to specify the resolution in the tile name.

        Returns
        -------
        list
            return a list of  the overlapped tiles' name. If not found, return empty list.

        Notes
        -----
            This is the internal function for the implementation.
        """
        # get the intersection of the area of interest and grid zone
        intersected_geom_area = area_geometry.Intersection(self.get_grid_zone_wgs84(grid))
        if not intersected_geom_area:
            return list()
        # The spatial reference need to be set again after intersection
        intersected_geom_area.AssignSpatialReference(area_geometry.GetSpatialReference())
        # transform the area of interest to the grid coordinate system
        grid_sr = osr.SpatialReference()
        grid_sr.ImportFromWkt(self.get_projection(grid))
        intersected_geom_area.TransformTo(grid_sr)
        # get envelope of the Geometry and cal the bounding tile of the envelope
        tile_xspan = self.tile_xspan
        tile_yspan = self.tile_yspan
        envelope = intersected_geom_area.GetEnvelope()
        x_min, x_max = (int(envelope[0]) / tile_xspan) * tile_xspan, (int(envelope[1]) / tile_xspan + 1) * tile_xspan
        y_min, y_max = (int(envelope[2]) / tile_yspan) * tile_yspan, (int(envelope[3]) / tile_yspan + 1) * tile_yspan
        # get overlapped tiles
        overlapped_tiles = list()
        for x in range(x_min, x_max, tile_xspan):
            for y in range(y_min, y_max, tile_yspan):
                # create rectangle of the tile
                edge = ogr.Geometry(ogr.wkbLinearRing)
                edge.AddPoint(x, y + tile_yspan)
                edge.AddPoint(x + tile_xspan, y + tile_yspan)
                edge.AddPoint(x + tile_xspan, y)
                edge.AddPoint(x, y)
                edge.CloseRings()
                geom_tile = ogr.Geometry(ogr.wkbPolygon)
                geom_tile.AddGeometry(edge)
                if geom_tile.Intersects(intersected_geom_area):
                    tile = self.identfy_tile(grid, [x, y], res)
                    overlapped_tiles.append(tile)
        return overlapped_tiles

    def resample(self, image, res, output_dir, grids=None, roi=None, outshortname=None, withtilenameprefix=True,
                 withtilenamesuffix=False, compress=True, resampling_type="bilinear", image_nodata=None, tile_nodata=None):
        """Resample the image to tiles.

        Parameters
        ----------
        image : string
            Image file path.
        res : int
            Resolution of output tiles.
        ouput_dir : string
            output path.
        outshortname : string
            The short name will be included in the output tiles.
        compress : bool
            The output tiles is compressed or not.
        resampling_type : string
            resampling method.
        tile_nodata: double
            The nodata value of tile.
        """
        if not outshortname:
            outshortname = os.path.splitext(os.path.basename(image))[0]
        ds = gdalport.open_image(image)
        proj = ds.projection()
        if not roi:
            extent = ds.get_extent()
            area = [(extent[0], extent[1]), (extent[2], extent[1]),
                    (extent[2], extent[3]), (extent[0], extent[3])]
            tiles = self.search_tiles(area, proj, grids=grids, res=res)
        else:
            tiles = self.search_tiles(roi, proj, grids=grids, res=res)

        for tile in tiles:
            tile_path = os.path.join(output_dir, tile)
            if not os.path.exists(tile_path):
                os.mkdir(tile_path)
            # make output filename
            outbasename = outshortname
            if withtilenameprefix:
                outbasename = "_".join((tile.split("_")[1], outshortname))
            if withtilenamesuffix:
                outbasename = "_".join((outshortname, tile.split("_")[1]))
            filename = os.path.join(tile_path, "".join((outbasename, ".tif")))
            # using python api to resample
#             if compress:
#                 option = ["COMPRESS=LZW"]
#             datatype = ds.get_raster_dtype(1)
#             tile_ds = self.create_dummy_dataset(tile, filename, datatype, options=option)
#             if tile_nodata:
#                 tile_ds.GetRasterBand(1).SetNoDataValue(tile_nodata)
#             gdal.ReprojectImage(ds.dataset, tile_ds, ds.projection(), tile_ds.GetProjection(),
#                                 gdalport.get_gdal_resampling_type(resampling_type))

            # using gdalwarp to resample
            tile_extent = self.get_tile_extent(tile)
            tile_project = self.get_projection(tile[0:2])
            options = {}
            if compress:
                options["co"] = "COMPRESS=LZW"
            if image_nodata:
                options["srcnodata"] = image_nodata
            if tile_nodata:
                options["dstnodata"] = tile_nodata
            gdalport.call_gdalwarp([image], filename, t_srs=tile_project,
                                   te=" ".join(map(str, tile_extent)), tr="{} -{}".format(res, res),
                                   of="GTiff", r=resampling_type, **options)
