##[for_modeler]=group
##Classified_Layer = raster
##Clumped_Layer = raster
##MMU = number 3
##Output_raster = output raster
Classified_Layer=raster(Classified_Layer,1)
Clumped_Layer=raster(Clumped_Layer,1)
pxarea=freq(Clumped_Layer)
df=as.data.frame(pxarea[pxarea[,2] <= MMU,])
df[,2]<-0
df2=as.data.frame(pxarea[pxarea[,2] > MMU,])
df2[,2]<-1
df3=data.frame(NA,0)
names(df)<-c("from","to")
names(df2)<-c("from","to")
names(df3)<-c("from","to")
df=rbind(df,df2,df3)
positive=df2[,1]
positive=na.omit(positive)
tmp <- calc(Clumped_Layer, fun=function(x,...) ifelse(x %in% positive, 1, 0), filename=rasterTmpFile(), datatype="INT1U")
Output_raster <- mask(tmp, Classified_Layer, maskvalue=NA, filename=rasterTmpFile(), datatype="INT2S")
