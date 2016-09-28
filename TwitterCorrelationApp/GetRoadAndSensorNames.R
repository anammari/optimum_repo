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
dataDir <- "NTISData\\"

GetRoadAndSensorNames <- function() {
  #Load the sensor data sets
  sensors_filenames <- list.dirs(dataDir,full.names=FALSE)
  sensorVec <- character(0)
  
  sumtabDf <- data.frame(
    highway = character(0),
    mId = character(0),
    mType = character(0),
    startDt = as.POSIXct(character()),
    endDt = as.POSIXct(character()),
    numMeasurement = numeric(0),
    stringsAsFactors = F
  )
  for (i in 1:length(sensors_filenames)) {
    namePart <- unlist(strsplit(sensors_filenames[i], "\\."))[1]
    highway <- unlist(strsplit(namePart, "_"))[2]
    mId <- unlist(strsplit(namePart, "_"))[1]
    name <- paste0(highway,"_",mId)
    sensorVec <- c(sensorVec,name)
  }
  sensorVec <- unique(sensorVec)
  sensorVec <- sort(sensorVec)
  return(sensorVec)
}