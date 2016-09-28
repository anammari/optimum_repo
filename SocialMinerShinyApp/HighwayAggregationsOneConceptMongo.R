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
# startStr <- "2016-07-01"
# endStr <- "2016-07-05"
# highwayCodes <- c("M1","M5")
plotHighwayTimeLines <- function(startStr, endStr, highwayCodes) {
  if (length(highwayCodes) < 1) {
    msg <- "highwayCodes must contains at least one highway"
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
  highwayTwitterAggsList <- list()
  if (mongo.is.connected(mongo) == TRUE) {
    for (i in 1:length(highwayCodes)) {
      #create dataframe to store the data
      highwayTwitterAggs = data.frame(
        gmt_date = as.POSIXct(character()),
        value = numeric(0),
        road = character(0),
        stringsAsFactors = F
      )
      queryList <- mongo.bson.from.list(list(
        'gmt_date' = list("$gte" = startDt,
                          "$lte" = endDt),
        "highway_code" = highwayCodes[i]
      ))
      tweets_count <-
        mongo.count(mongo,"Twitter.uk_accounts_highway_hr_agg",query = queryList)
      if (tweets_count > 0) {
        # flog.info("Total records to be fetched for highway %s: %s",highwayCodes[i], tweets_count)
        result <-
          mongo.find(mongo, "Twitter.uk_accounts_highway_hr_agg", query = queryList)
        while (mongo.cursor.next(result)) {
          tdDt <- .POSIXct(character())
          l <- list(mongo.bson.to.list(mongo.cursor.value(result)))
          tdDt <- l[[1]]$gmt_date
          value <- l[[1]]$value
          
          highwayTwitterAggs <- rbind(
            highwayTwitterAggs,
            data.frame(
              gmt_date = tdDt,
              value = value,
              road = highwayCodes[i],
              stringsAsFactors = FALSE
            )
          )
        }
        attr(highwayTwitterAggs$gmt_date, "tzone") <- "GMT"
        highwayTwitterAggs <-
          highwayTwitterAggs[with(highwayTwitterAggs, order(gmt_date)),]
        highwayTwitterAggsList[[i]] <- highwayTwitterAggs
      } else {
        #flog.info("No records found for highway %s",highwayCodes[i])
        msg <- paste0("No records found for highway ",highwayCodes[i])
        return(msg)
      }
    }
  }
  
  #Fill the hours which do not exist in the retrieved data with zero values
  highwayTwitterAggsFullList <- list()
  for (i in 1:length(highwayTwitterAggsList)) {
    highwayTwitterAggsFull <- data.frame(
      gmt_date = as.POSIXct(character()),
      value = numeric(0),
      road = character(0),
      stringsAsFactors = F
    )
    highwayTwitterAggs <- highwayTwitterAggsList[[i]]
    minDate <- startDt
    maxDate <- endDt
    road <- highwayTwitterAggs$road[1]
    while (minDate <= maxDate) {
      value <-
        highwayTwitterAggs[highwayTwitterAggs$gmt_date == minDate,c("value")]
      if (length(value) > 0) {
        highwayTwitterAggsFull <- rbind(
          highwayTwitterAggsFull,
          data.frame(
            gmt_date = minDate,
            value = value,
            road = road,
            stringsAsFactors = FALSE
          )
        )
      } else {
#         flog.info(
#           "No record found for highway %s on gmt_date: %s", road, strftime(minDate,"%Y-%m-%d %H:%M:%S",tz =
#                                                                              "GMT")
#         )
        highwayTwitterAggsFull <- rbind(
          highwayTwitterAggsFull,
          data.frame(
            gmt_date = minDate,
            value = 0,
            road = road,
            stringsAsFactors = FALSE
          )
        )
      }
      minDate <- minDate + 3600
    }
    attr(highwayTwitterAggsFull$gmt_date, "tzone") <- "GMT"
    highwayTwitterAggsFull <-
      highwayTwitterAggsFull[with(highwayTwitterAggsFull, order(gmt_date)),]
    highwayTwitterAggsFullList[[i]] <- highwayTwitterAggsFull
  }
  
  #create a dataframe of all the highway values
  valuesDF <- NULL
  for (i in 1:length(highwayTwitterAggsFullList)) {
    highwayTwitterAggsFull <- highwayTwitterAggsFullList[[i]]
    hway <- highwayTwitterAggsFull$road[1]
    if (is.null(valuesDF)) {
      valuesDF$col1 <- highwayTwitterAggsFull$value
      valuesDF <- as.data.frame(valuesDF)
      colnames(valuesDF) <- hway
    } else {
      col <- highwayTwitterAggsFull$value
      col <- as.data.frame(col)
      colnames(col) <- hway
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
  for (i in 1:length(highwayTwitterAggsFullList)) {
    highwayTwitterAggsFull <- highwayTwitterAggsFullList[[i]]
    newdf <-
      melt(highwayTwitterAggsFull[,c("gmt_date", "value")],'gmt_date')
    newdf$variable <-
      ifelse(newdf$variable == "value", highwayTwitterAggsFull$road[1], "value")
    meltedDF <- rbind(meltedDF,newdf)
  }
  
  colnames(meltedDF) <- c("gmt_date", "Highway", "value")
  attr(meltedDF$gmt_date, "tzone") <- "GMT"
  
  lower <-
    with(meltedDF,as.POSIXct(strftime(min(gmt_date),"%Y-%m-%d %H:%M:%S")))
  upper <-
    with(meltedDF,as.POSIXct(strftime(max(gmt_date),"%Y-%m-%d %H:%M:%S")))
  limits = c(lower,upper)
  timelineplot <- ggplot(meltedDF,aes(x = gmt_date,y = value)) +
    geom_line(size = 1.5,aes(colour = Highway)) +
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
    ggtitle("Highway Mentions in Tweets") +
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
