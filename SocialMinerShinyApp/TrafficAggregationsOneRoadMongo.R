#libraries
require(XLConnect)
require(rmongodb)
require(futile.logger)
require(tm)
require(rmongodb)
require(RCurl)
require(jsonlite)
require(wordcloud)
require(RColorBrewer)
require(xts)
require(reshape2)
require(plyr)
require(ggplot2)
require(scales)

Sys.setenv(TZ='GMT')

# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\SocialMinerShinyApp")
# startStr <- "2016-06-01"
# endStr <- "2016-06-05"
# trafficConcepts <- c("ROADWORKS","CONGESTION", "ACCIDENT")
# roadName <- "M1"
plotTrafficTimeLinesOneRoad <- function(startStr, endStr, trafficConcepts, roadName) {
  if (length(trafficConcepts) < 1) {
    msg <- "trafficConcepts must contains at least one highway"
    return(msg)
  }
  if (length(roadName) < 1) {
    msg <- "roadName cannot be empty"
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
  
  #connect to mongoDB
  mongo <- mongo.create(host = "optimum.euprojects.net:3368")
  
  #create a list to store all the dataframes
  trafficTwitterAggsList <- list()
  if (mongo.is.connected(mongo) == TRUE) {
    for (i in 1:length(trafficConcepts)) {
      #create dataframe to store the data
      trafficTwitterAggs = data.frame(
        gmt_date = as.POSIXct(character()),
        value = numeric(0),
        concept = character(0),
        stringsAsFactors = F
      )
      queryList <- mongo.bson.from.list(list(
        'gmt_date' = list("$gte" = startDt,
                          "$lte" = endDt),
        "traffic_concept" = trafficConcepts[i],
        "road" = roadName
      ))
      tweets_count <-
        mongo.count(mongo,"Twitter.uk_accounts_traffic_hr_agg_roads",query = queryList)
      if (tweets_count > 0) {
        #flog.info("Total records to be fetched for concept %s: %s",trafficConcepts[i], tweets_count)
        result <-
          mongo.find(mongo, "Twitter.uk_accounts_traffic_hr_agg_roads", query = queryList)
        while (mongo.cursor.next(result)) {
          tdDt <- .POSIXct(character())
          l <- list(mongo.bson.to.list(mongo.cursor.value(result)))
          tdDt <- l[[1]]$gmt_date
          value <- l[[1]]$value
          
          trafficTwitterAggs <- rbind(
            trafficTwitterAggs,
            data.frame(
              gmt_date = tdDt,
              value = value,
              concept = trafficConcepts[i],
              stringsAsFactors = FALSE
            )
          )
        }
        attr(trafficTwitterAggs$gmt_date, "tzone") <- "GMT"
        trafficTwitterAggs <-
          trafficTwitterAggs[with(trafficTwitterAggs, order(gmt_date)),]
        trafficTwitterAggsList[[i]] <- trafficTwitterAggs
      } else {
        #flog.info("No records found for concept %s",trafficConcepts[i])
        msg <- paste0("No records found for concept ",trafficConcepts[i])
        return(msg)
      }
    }
  }
  
  #Fill the hours which do not exist in the retrieved data with zero values
  trafficTwitterAggsFullList <- list()
  for (i in 1:length(trafficTwitterAggsList)) {
    trafficTwitterAggsFull <- data.frame(
      gmt_date = as.POSIXct(character()),
      value = numeric(0),
      concept = character(0),
      stringsAsFactors = F
    )
    trafficTwitterAggs <- trafficTwitterAggsList[[i]]
    minDate <- startDt
    maxDate <- endDt
    concept <- trafficTwitterAggs$concept[1]
    while (minDate <= maxDate) {
      value <-
        trafficTwitterAggs[trafficTwitterAggs$gmt_date == minDate,c("value")]
      if (length(value) > 0) {
        trafficTwitterAggsFull <- rbind(
          trafficTwitterAggsFull,
          data.frame(
            gmt_date = minDate,
            value = value,
            concept = concept,
            stringsAsFactors = FALSE
          )
        )
      } else {
#         flog.info(
#           "No record found for concept %s on gmt_date: %s", concept, strftime(minDate,"%Y-%m-%d %H:%M:%S",tz =
#                                                                              "GMT")
#         )
        trafficTwitterAggsFull <- rbind(
          trafficTwitterAggsFull,
          data.frame(
            gmt_date = minDate,
            value = 0,
            concept = concept,
            stringsAsFactors = FALSE
          )
        )
      }
      minDate <- minDate + 3600
    }
    attr(trafficTwitterAggsFull$gmt_date, "tzone") <- "GMT"
    trafficTwitterAggsFull <-
      trafficTwitterAggsFull[with(trafficTwitterAggsFull, order(gmt_date)),]
    trafficTwitterAggsFullList[[i]] <- trafficTwitterAggsFull
  }
  
  #create a dataframe of all the traffic concept values
  valuesDF <- NULL
  for (i in 1:length(trafficTwitterAggsFullList)) {
    trafficTwitterAggsFull <- trafficTwitterAggsFullList[[i]]
    concept <- trafficTwitterAggsFull$concept[1]
    if (is.null(valuesDF)) {
      valuesDF$col1 <- trafficTwitterAggsFull$value
      valuesDF <- as.data.frame(valuesDF)
      colnames(valuesDF) <- concept
    } else {
      col <- trafficTwitterAggsFull$value
      col <- as.data.frame(col)
      colnames(col) <- concept
      valuesDF <- as.data.frame(cbind(valuesDF,col))
    }
  }
  
  #create the melted dataframes and merge them all into one data frame for the plot
  meltedDF <- data.frame(
    gmt_date = as.POSIXct(character()),
    variable = character(0),
    value = numeric(0),
    stringsAsFactors = F
  )
  for (i in 1:length(trafficTwitterAggsFullList)) {
    trafficTwitterAggsFull <- trafficTwitterAggsFullList[[i]]
    newdf <-
      melt(trafficTwitterAggsFull[,c("gmt_date", "value")],'gmt_date')
    newdf$variable <-
      ifelse(newdf$variable == "value", trafficTwitterAggsFull$concept[1], "value")
    meltedDF <- rbind(meltedDF,newdf)
  }
  
  colnames(meltedDF) <- c("gmt_date", "Concept", "value")
  attr(meltedDF$gmt_date, "tzone") <- "GMT"
  
  lower <-
    with(meltedDF,as.POSIXct(strftime(min(gmt_date),"%Y-%m-%d %H:%M:%S")))
  upper <-
    with(meltedDF,as.POSIXct(strftime(max(gmt_date),"%Y-%m-%d %H:%M:%S")))
  limits = c(lower,upper)
  timelineplot <- ggplot(meltedDF,aes(x = gmt_date,y = value)) +
    geom_line(size = 1.5,aes(colour = Concept)) +
    scale_fill_brewer(palette = "Set1") +
    xlab("Time (Hours)") +
    ylab("Number of tweets") +
    scale_x_datetime(
      date_breaks = ("2 hour"),
      date_labels = "%b %d %H",
      limits = limits
    ) +
    scale_y_discrete(breaks = seq(min(meltedDF$value), max(meltedDF$value) *
                                    2, by = 5), labels = comma) +
    ggtitle(paste0("Traffic Concept Mentions in Tweets for Road ",roadName)) +
    theme(
      axis.text.x = element_text(
        angle = 45, hjust = 1, size = 8
      ),
      axis.text.y = element_text(size = 10),
      legend.text = element_text(size = 12)
    )
  returnList <- list()
  returnList[[1]] <- timelineplot
  returnList[[2]] <- valuesDF
  return(returnList)
}
