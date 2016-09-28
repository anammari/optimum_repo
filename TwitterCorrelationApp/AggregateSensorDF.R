Sys.setenv(TZ='GMT')
require(xts)
require(zoo)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

trim <- function (x) gsub("^\\s+|\\s+$", "", x)

list.dirs <- function(path, pattern=NULL, all.dirs=FALSE, full.names=TRUE, ignore.case=FALSE) {
  # use full.names=TRUE to pass to file.info
  all <- list.files(path, pattern, all.dirs,
                    full.names=TRUE, recursive=FALSE, ignore.case=TRUE)
  # determine whether to return full names or just dir names
  if(isTRUE(full.names))
    return(all)
  else
    return(basename(all))
}
#for testing
# selectMType <- "flow"

AggregateSensorDF <- function(sensorDf,mType) {
  if (is.null(sensorDf)) {
    msg <- "sensor Data Frame cannot be Null"
    return(msg)
  }
  if (class(sensorDf) != "data.frame") {
    msg <- "sensorDf class must be data.frame"
    return(msg)
  }
  if (is.null(mType)) {
    msg <- "Measurment Type cannot be Null"
    return(msg)
  }
  #aggregate sensor data
  sensor.ts <- xts(sensorDf[,-1], order.by=as.POSIXct(sensorDf$datetime))
  if (mType == "flow") {
    aggs.ts <- period.apply(sensor.ts, endpoints(sensor.ts, "hours"), function(x) sum(x))
  }
  else {
    aggs.ts <- period.apply(sensor.ts, endpoints(sensor.ts, "hours"), function(x) mean(x))
  }
  
  aggs.tsAvgAggs = data.frame(
    datetime = as.POSIXct(index(aggs.ts)) - 3540,
    value = aggs.ts[,c(1)],
    stringsAsFactors = F
  )
  row.names(aggs.tsAvgAggs) <- NULL
  
  startDt <- min(aggs.tsAvgAggs$datetime)
  endDt <- max(aggs.tsAvgAggs$datetime)
  aggSensorData <- list()
  aggSensorData[[1]] <- aggs.tsAvgAggs
  aggSensorData[[2]] <- startDt
  aggSensorData[[3]] <- endDt
  return(aggSensorData)
}