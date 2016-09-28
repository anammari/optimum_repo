Sys.setenv(TZ='GMT')
require(rmongodb)
require(futile.logger)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

#from the 3375 VM:
#hostPort <- "192.168.3.50:27017"
#from anywhere else:
hostPort <- "optimum.euprojects.net:3368"

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

######For Testing#######
########################
# startStr <- "2016-04-15"
# endStr <- "2016-04-30"
# roadSensId <- "M6_7CC244D415714013A78F98B7FD3AB216"
# TwitterDT <- "RMGeneral"
# trafficConceptsCor <- NULL
# #convert times data stypes
# startStr <- paste0(startStr,"T00:00:00")
# endStr <- paste0(endStr,"T23:59:59")
# startDt <-
#   strptime(startStr, format = "%Y-%m-%dT%H:%M:%S", tz = "GMT")
# endDt <-
#   strptime(endStr, format = "%Y-%m-%dT%H:%M:%S", tz = "GMT")
########################

GetTwitterDF <- function(startDt, endDt, roadSensId, TwitterDT, trafficConceptsCor) {
  if (is.null(TwitterDT)) {
    msg <- "Twitter Data Type cannot be Null"
    return(msg)
  }
  if (is.null(roadSensId)) {
    msg <- "road_sensorId cannot be Null"
    return(msg)
  }
  if (TwitterDT == "RMConcept" & is.null(trafficConceptsCor)) {
    msg <- "Traffic Concept cannot be Null"
    return(msg)
  }
  if (endDt <= startDt) {
    msg <- "start date must be older than end date"
    return(msg)
  }
  #decide which DB and collection to retrieve the data from
  if (TwitterDT == "RMGeneral") {
    twitterDBCol <- "Twitter.uk_accounts_highway_hr_agg"
  } else {
    twitterDBCol <- "Twitter.uk_accounts_traffic_hr_agg_roads"
  }
  #extract highway
  highway <- unlist(strsplit(roadSensId, "_"))[1]
  #create dataframe to store the data
  highwayTwitterAggs = data.frame(
    gmt_date = as.POSIXct(character()),
    value = numeric(0),
    stringsAsFactors = F
  )
  #connect to mongoDB
  mongo <- mongo.create(host = hostPort)
  
  if (mongo.is.connected(mongo) == TRUE) {
    if (twitterDBCol == "Twitter.uk_accounts_highway_hr_agg") {
      queryList <- mongo.bson.from.list(
        list('gmt_date' = list(
          "$gte" = startDt,
          "$lte" = endDt
        ),
        "highway_code" = highway))
    } else {
      queryList <- mongo.bson.from.list(
        list('gmt_date' = list(
          "$gte" = startDt,
          "$lte" = endDt
        ),
        "road" = highway,
        "traffic_concept" = trafficConceptsCor))
    }
    tweets_count <- mongo.count(mongo,twitterDBCol,query=queryList)
    if (tweets_count > 0) {
      #flog.info("Total records to be fetched for %s: %s", highway, tweets_count)
      result <- mongo.find(mongo, twitterDBCol, query = queryList)
      while (mongo.cursor.next(result)) {
        tdDt <- .POSIXct(character())
        l <- list(mongo.bson.to.list(mongo.cursor.value(result)))
        tdDt <- l[[1]]$gmt_date
        value <- l[[1]]$value
        
        highwayTwitterAggs <-rbind(highwayTwitterAggs,
                                   data.frame(gmt_date = tdDt,
                                              value = value,
                                              stringsAsFactors = FALSE)
        )
      }
      attr(highwayTwitterAggs$gmt_date, "tzone") <- "GMT"
      highwayTwitterAggs <- highwayTwitterAggs[with(highwayTwitterAggs, order(gmt_date)), ]
    } else {
      #flog.info("No records found from twitter for highway %s", highway)
      highwayTwitterAggs <-rbind(highwayTwitterAggs,
                                 data.frame(gmt_date = startDt,
                                            value = 0,
                                            stringsAsFactors = FALSE))
    }
  }
  #fill the unavailable twitter dataset hours with zeros
  highwayTwitterAggsFull <- data.frame(
    gmt_date = as.POSIXct(character()),
    value = numeric(0),
    stringsAsFactors = F
  )
  
  minDateTwit <- startDt
  maxDateTwit <- endDt
  while (minDateTwit <= maxDateTwit) {
    value <- highwayTwitterAggs[highwayTwitterAggs$gmt_date == minDateTwit,c("value")]
    if (length(value) > 0) {
      highwayTwitterAggsFull <-rbind(highwayTwitterAggsFull,
                                     data.frame(gmt_date = minDateTwit,
                                                value = value,
                                                stringsAsFactors = FALSE)
      )
    } else {
      #flog.info("No record found in gmt_date: %s", strftime(minDateTwit,"%Y-%m-%d %H:%M:%S",tz="GMT"))
      highwayTwitterAggsFull <-rbind(highwayTwitterAggsFull,
                                     data.frame(gmt_date = minDateTwit,
                                                value = 0,
                                                stringsAsFactors = FALSE)
      )
    }
    minDateTwit <- minDateTwit + 3600
  }
  attr(highwayTwitterAggsFull$gmt_date, "tzone") <- "GMT"
  return(highwayTwitterAggsFull)
}