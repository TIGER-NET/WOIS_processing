##[Classification]=group 
##Layer = raster
##Nodata_value = number 0
##Lower_than = boolean True
##Tile_size = number 200
##Classified_raster = output raster
#tryCatch(find.package("rgdal"), error=function(e) install.packages("rgdal"))
#library(rgdal)
# Otsu thresholding algorithm
library(tcltk)
Layer <- raster(Layer,1)
otsu <- function(x, na.rm = TRUE)
{
	if (na.rm) x <- na.omit(x)
	if (!is.integer(x)) x <- round(x)
	
	#h <- hist(x, plot = FALSE)
	L <- length(x)
	tt <- table(x)
	vals <- as.integer(names(tt))
	
	wB <- function(p, ct, vals) {
		return(sum(ct[vals < p]) / L)
	}
	wF <- function(p, ct, vals) {
		return(sum(ct[vals >= p]) / L)
	}
	
	vB <- function(p, ct, vals, x) {
		wB(p, ct, vals) * wF(p, ct, vals) * ((mean(x[x < p])-mean(x[x >= p]))^2)
	}
	o <- optimize(vB, c(min(x),max(x)), tt, vals, x, maximum = TRUE)
	return(o$maximum)
}
# Split-based Otsu thresholding
otsuSplitThreshold <- function(img, splitTileSize, na.rm = TRUE) {
	# retrieve image statistics and scale to gray levels
	imgmean <- cellStats(img, "mean", na.rm=TRUE)
	imgmax <- cellStats(img, "max")
	imgmin <- cellStats(img, "min")
	imggraymean <- (imgmean-imgmin) / abs(imgmax-imgmin) * 255
	# compute Otsu threshold for each image tile
	nTilesY <- floor(nrow(img) / splitTileSize)
	aspectratio <- max(1, round(nrow(img)/ncol(img)), na.rm = TRUE)
	nTilesX <- floor(ncol(img) / splitTileSize)
	#thr <- vector("numeric", nTilesY * nTilesX)
	tilestats <- as.data.frame(matrix(NA, nr=nTilesY*nTilesX, 6))
	names(tilestats) <- c("i","j","CV","R","nNoData","otsu")
	for (i in 1:nTilesY) {
		cat("row",i,"...\n")
		rowmin <- max(1,(i-1)*splitTileSize+1)
		m <- getValues(img, row = rowmin, nrows = splitTileSize, format = "matrix")
		for (j in 1:nTilesX) {
			colmin <- max(1,(j-1)*splitTileSize/aspectratio+1)
			colmax <- min(ncol(img),(j-1)*splitTileSize/aspectratio+splitTileSize/aspectratio)
			v <- as.vector(m[,colmin:colmax])
			if (any(!is.na(v))) {
				v.gray <- (v - imgmin) / (abs(imgmax-imgmin)) * 255
				k <- (i-1)*nTilesX+j
				tilestats[k,1] <- i
				tilestats[k,2] <- j
				tilestats[k,3] <- abs(sd(v.gray, na.rm=TRUE) / mean(v.gray, na.rm=TRUE))
				tilestats[k,4] <- mean(v.gray, na.rm=TRUE) / imggraymean
				tilestats[k,5] <- length(which(is.na(v)))
				if (tilestats[k,5] < splitTileSize^2/100 & tilestats[k,3] >= 0.7 & tilestats[k,4] >= 0.4 & tilestats[k,4] <= 0.9)
					tilestats[k,6] <- otsu(v.gray)
			}
		}
	}
  	# rescale from gray levels
	tilestats$otsu <- tilestats$otsu/255 * (abs(imgmax-imgmin)) + imgmin
	return(tilestats)
}
# Process image
NAvalue(Layer) <- Nodata_value
cat("Converting to linear scale...\n")
Layer.lin <- calc(Layer, function(x) 10^(x/10))
cat("Threshold computation...\n")
tilestats <- otsuSplitThreshold(Layer.lin, Tile_size)
# use minimum as threshold theta
theta <- min(tilestats$otsu, na.rm = TRUE)
print(summary(tilestats))
if (!is.finite(theta)) {
	cat("No threshold could be computed.\n")
	cat("Returning empty raster.\n")
	Classified_raster <- raster(Layer.lin)
	tt <- tk_messageBox(type="ok", message="No threshold could be computed. Returning empty raster.",
			caption="Automatic Split-based Otsu Threshold")
} else {
	cat("Automatically computed threshold:", 10*log10(theta), "\n")
	if (Lower_than) {
		Classified_raster <- Layer.lin < theta
	} else {
		Classified_raster <- Layer.lin > theta
	}
}
