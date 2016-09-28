# Sys.setlocale('LC_ALL','C')
Sys.setenv(TZ='GMT')
source("GetRoadAndSensorNames.R")
source("GetMergedDF.R")
source("PlotCorrs.R")
source("PlotReg.R")
source("PlotTimeLines.R")
source("PlotLaggedScatters.R")
library(shiny)

ui <- shinyUI(fluidPage(
  titlePanel("OPTIMUM Traffic Forecasting Engine: Sensor-Twitter Correlation"),
  tabsetPanel(
    tabPanel("Sensors Correlation",
       sidebarLayout(
         sidebarPanel(
           h4('Common Parameters:'),
           dateInput("StartDateCor", "Start Date:"),
           dateInput("EndtDateCor", "End Date:"),
           checkboxInput("ACF", label = "Autocorrelation Function (ACF) Plots", value = FALSE),
           checkboxInput("CCF", label = "Cross-Correlation Function (CCF) Plot", value = FALSE),
           checkboxInput("Reg", label = "Linear Regression Scatter Plot", value = FALSE),
           checkboxInput("LaggedScatters", label = "Past Twitter Lags vs Sensor Series", value = FALSE),
           checkboxInput("timePlots", label = "Time Series Plots", value = FALSE),
           h4('Sensor Parameters:'),
           selectInput("selectRoadSensorId", label = "Select Road_SensorID:", 
                       choices = GetRoadAndSensorNames(), selectize=FALSE,
                       multiple=FALSE),
           selectInput("selectMType", label = "Select Sensor Measurement Type:", 
                       choices = list("Flow" = "flow", "Average Speed" = "speed"), 
                       multiple=FALSE),
           h4('Twitter Parameters:'),
           radioButtons("TwitterDT", "Select Twitter Feature:",
                        c("Road Mention for all Traffic Concepts" = "RMGeneral",
                          "Road Mentions for Specific Traffic Concept" = "RMConcept"
                        )),
           selectInput(
             "trafficConceptsCor", "Traffic Concepts",
             list(
               "ACCIDENT" = "ACCIDENT",
               "BARRIER" = "BARRIER",
               "CLOSED" = "CLOSED",
               "CONGESTION" = "CONGESTION",
               "DELAY" = "DELAY",
               "MANAGEMENT" = "MANAGEMENT",
               "OPENED" = "OPENED",
               "REPAIRS" = "REPAIRS",
               "ROADWORKS" = "ROADWORKS",
               "STUCK" = "STUCK",
               "TRAFFIC" = "TRAFFIC"
             ), multiple=FALSE
           ),
           selectInput(
             "maxLag", "Maximum Lag (hours)",
             list(
               "1" = "1","2" = "2","3" = "3","4" = "4","5" = "5","6" = "6","7" = "7","8" = "8","9" = "9","10" = "10",
               "11" = "11","12" = "12","13" = "13","14" = "14","15" = "15","16" = "16","17" = "17","18" = "18","19" = "19","20" = "20",
               "21" = "21","22" = "22","23" = "23","24" = "24","25" = "25"
             ), multiple=FALSE
           ),
           actionButton("plotCorBtn", "Plot Correlations")
         ),
         mainPanel(
           #     verbatimTextOutput("start"),
           #     verbatimTextOutput("end"),
           #     verbatimTextOutput("vector"),
           #     verbatimTextOutput("button"),
           style = "background-color:Azure;",
           h4('Sensor-Twitter Correlation Service', align = "center"),
           h5("This service is used to assist the user in investigating the correlation between two time-series data sets of 
              different sources. The first is sets of traffic sensor measurements. The second is Twitter-derived series."),
           h5("Sensor measurements can be either the sum of traffic flows or the average traffic speed. The Twitter-derived series can be 
              either the hourly aggregates of the road mentions in general, or the hourly aggregates of the road mentions for a specific
              traffic concept."),
           h5("The service produces autocorrelation function (acf) plot for each series, cross-correlation function (ccf) plot for
              the two series showing which dominant Twitter lag that has the maximum correlation with the sensor series, scatter plot 
              of the two series with linear regression R-squared and Pearson correlation coefficient, scatter plots of lagged Twitter 
              features and the sensor series, and time plots of the two series."),
           h5("Note: Available sensor data is between 13 April and 21 June 2016", style = "color:red"),
           conditionalPanel(condition="sum(c(input.ACF,input.CCF)) > 0",       
                            plotOutput("corrPlots", height = 800)
           ),
           conditionalPanel(condition="input.Reg == 1",       
                            plotOutput("regPlot", height = 600)
           ),
           conditionalPanel(condition="input.LaggedScatters == 1",       
                            plotOutput("laggedScatterPlots", height = 600)
           ),
           conditionalPanel(condition="input.timePlots == 1",       
                            plotOutput("timePlot", height = 600)
           )
         )
    )
  )
  )
)
)

server <- function(input, output) {
  StartDateCor <- reactive({input$StartDateCor})
  EndtDateCor <- reactive({input$EndtDateCor})
  ACF <- reactive({input$ACF})
  CCF <- reactive({input$CCF})
  Reg <- reactive({input$Reg})
  LaggedScatters <- reactive({input$LaggedScatters})
  timePlots <- reactive({input$timePlots})
  RoadSensorId <- reactive({input$selectRoadSensorId}) 
  MType <- reactive({input$selectMType})
  TwitterDT <- reactive({input$TwitterDT})
  trafficConceptsCor <- reactive({input$trafficConceptsCor})
  maxLag <- reactive({as.numeric(input$maxLag)})
  
  mergedDt <- eventReactive(input$plotCorBtn, {
    GetMergedDF(StartDateCor(), EndtDateCor(), RoadSensorId(), MType(), TwitterDT(), trafficConceptsCor())
  })
  
  output$corrPlots <- renderPlot({
    if (ACF() & CCF()) {
      print(PlotCorrs(mergedDt(),1,1,maxLag()))
    } else if (ACF()) {
      print(PlotCorrs(mergedDt(),1,0,maxLag()))
    } else if (CCF()) {
      print(PlotCorrs(mergedDt(),0,1,maxLag()))
    }
  })
  
  output$regPlot <- renderPlot({
    if (Reg()) {
      print(PlotReg(mergedDt()))
    }
  })
  
  output$laggedScatterPlots <- renderPlot({
    if (LaggedScatters()) {
      print(PlotLaggedScatters(mergedDt(), maxLag()))
    }
  })
  
  output$timePlot <- renderPlot({
    if (timePlots()) {
      print(PlotTimeLines(mergedDt()))
    }
  })
}

shinyApp(ui = ui, server = server)