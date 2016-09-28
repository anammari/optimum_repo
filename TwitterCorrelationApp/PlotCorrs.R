Sys.setenv(TZ='GMT')
require(xts)
require(zoo)
require(ggplot2)
require(graphics)
require(astsa)
require(scales)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

Find_Max_CCF<- function(a,b,maxLag)
{
  d <- ccf(a, b, plot = FALSE, lag.max=maxLag)
  cor = d$acf[,,1]
  lag = d$lag[,,1]
  res = data.frame(cor,lag)
  res = res[res$lag < 0,]
  res_max = res[which.max(abs(res$cor)),]
  return(res_max)
}

#For testing
ACF <- 1
CCF <- 1
maxLag <- 24

PlotCorrs <- function(mergedDt,ACF,CCF,maxLag) {
  if (is.null(mergedDt)) {
    msg <- "mergedDt Data Frame cannot be Null"
    return(msg)
  }
  if (class(mergedDt) != "data.frame") {
    msg <- "mergedDt class must be data.frame"
    return(msg)
  }
  #check that there must be at least 1 plot
  numPlots <- sum(c(ACF,CCF))
  if (numPlots < 1) {
    msg <- "There must be at least 1 plot to draw"
    return(msg)
  }
  #decide how many plots to produce for the acf, ccf plots
  if (ACF & CCF) {
    par(mfrow=c(3,1))
  } else if (ACF) {
    par(mfrow=c(2,1))
  } else {
    par(mfrow=c(1,1))
  }
  
  if (ACF) {
    acf(mergedDt$sensorV, lag.max=maxLag, main="Sensor Values", xlim=c(0,maxLag), plot = TRUE)
    acf(mergedDt$twitterV, lag.max=maxLag, main="Twitter Values", xlim=c(0,maxLag), plot = TRUE)
  }
  if (CCF) {
    ccf.DF <- Find_Max_CCF(mergedDt$twitterV, mergedDt$sensorV, maxLag)
    domLag <- ccf.DF$lag
    corr <- round(ccf.DF$cor,3)
    ccf(mergedDt$twitterV, mergedDt$sensorV, lag.max=maxLag, 
        main=paste0("Cross-Correlation Plot \n Dominant Lag: ",domLag," - Correlation: ",corr)
        , ylab="CCF", plot = TRUE, xlim=c(-1 * maxLag, maxLag))
  }
}