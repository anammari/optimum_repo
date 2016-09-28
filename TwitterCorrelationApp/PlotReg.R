Sys.setenv(TZ='GMT')
require(xts)
require(zoo)
require(ggplot2)
require(graphics)
require(astsa)
require(scales)
# setwd("C:\\Users\\Ahmad\\Dropbox\\Work\\WolverhamptonUni\\Optimum\\social_media\\twitter\\ShinyApps\\TwitterCorrelationApp")

lm_eqn <- function(df){
  df <- df[,c(2,3)]
  colnames(df) <- c("y","x")
  m <- lm(y ~ x, df);
  eq <- substitute(italic(y) == a + b %.% italic(x)*","~~italic(r)^2~"="~r2, 
                   list(a = format(coef(m)[1], digits = 2), 
                        b = format(coef(m)[2], digits = 2), 
                        r2 = format(summary(m)$r.squared, digits = 3)))
  as.character(as.expression(eq));                 
}

PlotReg <- function(mergedDt) {
  if (is.null(mergedDt)) {
    msg <- "mergedDt Data Frame cannot be Null"
    return(msg)
  }
  if (class(mergedDt) != "data.frame") {
    msg <- "mergedDt class must be data.frame"
    return(msg)
  }
  corr <- round(cor(mergedDt$twitterV, mergedDt$sensorV),3)
  ggplot(mergedDt, aes(x=twitterV, y=sensorV)) + 
    geom_smooth(method = "lm", se=FALSE, color="black", formula = y ~ x) +
    geom_point(shape=20, size = 5) +       
    xlab("Hourly mentions of Twitter events") +
    ylab("Hourly sensor readings") +
    #scale_y_discrete(breaks = seq(min(pol_dist$volume), max(pol_dist$volume), by = 100), labels = comma) + 
    ggtitle(paste0("Twitter Traffic Events VS Sensor Readings\nCorrelation Coeficient: ",corr)) + 
    theme(plot.title = element_text(color="#666666", face="bold", size=14),
          axis.text.x=element_text(size=14), 
          axis.text.y=element_text(size=14),
          axis.title.x=element_text(size=14,face="bold"),
          axis.title.y=element_text(size=14,face="bold")) +
    geom_text(x = median(unique(mergedDt$twitterV)), y = median(unique(mergedDt$sensorV)), 
              label = lm_eqn(mergedDt), size=9, colour = "red", parse = TRUE)
}