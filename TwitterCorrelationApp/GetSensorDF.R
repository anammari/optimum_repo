Sys.setenv(TZ='GMT')
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

#sensor data directory
dataDir <- "NTISData/"

#For testing
# startStr <- "2016-05-25"
# endStr <- "2016-05-30"
# roadSensId <- "A5_C6E971CAD44E789BE0433CC411ACCCEA"
# mType <- "speed"

GetSensorDF <- function(startStr, endStr, roadSensId, mType) {
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
  roadPart <- unlist(strsplit(roadSensId, "_"))[1]
  mIdPart <- unlist(strsplit(roadSensId, "_"))[2]
  filename <- paste0(mIdPart,"_",roadPart,"_",mType,".csv")
  sensors_full_filename <- paste0(dataDir,filename)
  data <- read.table(file = sensors_full_filename, sep = " ", header = FALSE, fileEncoding = "utf8")
  colnames(data) <- c("datetime","V")
  data$datetime <- strptime(data$datetime, format = "%Y-%m-%dT%H:%M:%S") - 3600
  attr(data$datetime, "tzone") <- "GMT"
  data <- data[with(data, order(datetime)), ]
  dataMinDate <- min(data$datetime)
  dataMaxDate <- max(data$datetime)
  num_records <- nrow(data[with(data, data$datetime >= startDt & data$datetime <= endDt),])
  if (num_records == 0) {
    msg <- "No data retrieved for the selected time window"
    return(msg)
  }
  data <- data[with(data, data$datetime >= startDt & data$datetime <= endDt),]
  return(data)
}