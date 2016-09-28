Sys.setenv(TZ='GMT')
require(xts)
require(zoo)
require(ggplot2)
require(graphics)
require(astsa)
require(scales)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

#For testing
# maxLag <- 24

PlotLaggedScatters <- function(mergedDt,maxLag) {
  if (is.null(mergedDt)) {
    msg <- "mergedDt Data Frame cannot be Null"
    return(msg)
  }
  if (class(mergedDt) != "data.frame") {
    msg <- "mergedDt class must be data.frame"
    return(msg)
  }
  lag2.plot (mergedDt$twitterV, mergedDt$sensorV, max.lag = maxLag, corr = F, smooth = T)
}