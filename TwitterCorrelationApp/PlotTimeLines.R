Sys.setenv(TZ='GMT')
require(xts)
require(zoo)
require(ggplot2)
require(graphics)
require(astsa)
require(plyr)
require(scales)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

myXBreaks <- function(x){
  xList <- list()
  d <- round(abs(difftime(min(x),max(x),units="days")))
  dNum <- as(d,"numeric")
  if (dNum <= 7) {
    xlabStr <- "Time (Hours)"
    dateBreaks <- switch(dNum,
                         "1 hour",
                         "2 hours",
                         "3 hours",
                         "4 hours",
                         "6 hours",
                         "6 hours",
                         "6 hours"
    )
    dateLabels = "%B %d %H"
  } else if (dNum <= 14) {
    xlabStr <- "Time (Hours)"
    dateBreaks <- "12 hours"
    dateLabels = "%B %d %H"
  } else {
    xlabStr <- "Time (Hours)"
    dateBreaks <- "24 hours"
    dateLabels = "%B %d %H"
  }
  xList[[1]] <- xlabStr
  xList[[2]] <- dateBreaks
  xList[[3]] <- dateLabels
  
  return(xList)
}

PlotTimeLines <- function(mergedDt) {
  if (is.null(mergedDt)) {
    msg <- "mergedDt Data Frame cannot be Null"
    return(msg)
  }
  if (class(mergedDt) != "data.frame") {
    msg <- "mergedDt class must be data.frame"
    return(msg)
  }
  
  minDate <- min(mergedDt$datetime)
  maxDate <- max(mergedDt$datetime)
  limits = c(minDate,maxDate)
  xList <- myXBreaks(mergedDt$datetime)
  ggplot(mergedDt, aes(datetime)) + 
    geom_line(size = 1.25, aes(y = sensorV, colour = "sensorV")) +
    geom_line(size = 1.25, aes(y = twitterV, colour = "twitterV")) +
    scale_colour_discrete("Series") +
    scale_x_datetime( date_breaks = (xList[[2]]),
                      date_labels = xList[[3]],
                      limits = limits
                      ) + 
    xlab(xList[[1]]) + 
    ylab("Hourly Aggregates (Log Transformed)") +
    ggtitle("Sensor Vs. Twitter Time Plots") +
    scale_y_continuous(trans='log2', labels=comma) +
    theme(
      plot.title = element_text(colour = "red", size = 20),
      axis.text.x = element_text(
        angle = 45, hjust = 1, size = 16
      ),
      axis.title.x = element_text(size = 16, colour="blue"),
      axis.text.y = element_text(size = 16),
      axis.title.y = element_text(size = 16, colour="blue"),
      legend.text = element_text(size = 16),
      legend.title = element_text(colour="blue", size=16, face="bold")
      )
}