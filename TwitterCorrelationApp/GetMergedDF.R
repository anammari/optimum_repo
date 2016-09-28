source("GetSensorDF.R")
source("GetTwitterDF.R")
source("AggregateSensorDF.R")

Sys.setenv(TZ='GMT')
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

#For testing
# startStr <- "2016-05-25"
# endStr <- "2016-05-30"
# roadSensId <- "A5_C6E971CAD44E789BE0433CC411ACCCEA"
# mType <- "flow"

GetMergedDF <- function(startStr, endStr, roadSensId, mType, TwitterDT, trafficConceptsCor) {
  if (is.null(mType)) {
    msg <- "Measurement Type cannot be Null"
    return(msg)
  }
  if (is.null(roadSensId)) {
    msg <- "road_sensorId cannot be Null"
    return(msg)
  }
  startStr <- paste0(startStr,"T00:00:00")
  endStr <- paste0(endStr,"T23:59:59")
  startDt <-
    strptime(startStr, format = "%Y-%m-%dT%H:%M:%S", tz = "GMT")
  endDt <-
    strptime(endStr, format = "%Y-%m-%dT%H:%M:%S", tz = "GMT")
  if (endDt <= startStr) {
    msg <- "start date must be older than end date"
    return(msg)
  }
  if (is.null(TwitterDT)) {
    msg <- "Twitter Data Type cannot be Null"
    return(msg)
  }
  if (TwitterDT == "RMConcept" & is.null(trafficConceptsCor)) {
    msg <- "Traffic Concept cannot be Null"
    return(msg)
  }
  sensorDf <- GetSensorDF(startStr, endStr, roadSensId, mType)
  if (class(sensorDf) != "data.frame") {
    msg <- "sensorDf class must be data.frame"
    return(msg)
  }
  aggSensorData <- AggregateSensorDF(sensorDf,mType)
  aggSensorDF <- aggSensorData[[1]]
  startDt <- aggSensorData[[2]]
  endDt <- aggSensorData[[3]]
  TwitterAggsFull <- GetTwitterDF(startDt, endDt, roadSensId, TwitterDT, trafficConceptsCor)
  #merge the 2 datasets
  mergedDt <- merge(aggSensorDF, TwitterAggsFull, by.x = "datetime", by.y = "gmt_date")
  colnames(mergedDt) <- c("datetime","sensorV","twitterV")
  return(mergedDt)
}