# Sys.setlocale('LC_ALL','C')
Sys.setenv(TZ='GMT')
source("HighwayAggregationsMongo.R")
source("TrafficAggregationsMongo.R")
source("TrafficAggregationsOneRoadMongo.R")
library(shiny)

ui <- shinyUI(fluidPage(
  titlePanel("Traffic Forecasting Engine - Social Miner Demo"),
  tabsetPanel(
    tabPanel("Highway Mentions",
      sidebarLayout(
        sidebarPanel(
          h4('Select start date, end date, and highways'),
          dateInput("StartDate", "Start Date:"),
          dateInput("EndtDate", "End Date:"),
          checkboxGroupInput(
            "highwayCodes", "Highways",
            c(
              "M1" = "M1",
              "M5" = "M5",
              "M6" = "M6",
              "M25" = "M25",
              "M40" = "M40",
              "M62" = "M62",
              "A1" = "A1",
              "A46" = "A46",
              "A45" = "A45",
              "A5" = "A5"
            )
          ),
          actionButton("plotTL", "Plot Timelines"),
          checkboxInput("summary", label = "Show Highways Summary Statistics", value = FALSE)
        ),
        mainPanel(
          #     verbatimTextOutput("start"),
          #     verbatimTextOutput("end"),
          #     verbatimTextOutput("vector"),
          #     verbatimTextOutput("button"),
          style = "background-color:Pink;",
          h4('Highway Mentions Service', align = "center"),
          h4("This service is used to visualize the volume of tweets that mention one or more UK roads per hour within a specified 
            time window."), 
          h4("The page also shows basic statistics about the timeline of each selected highway."),
          plotOutput("newPlot"),
          verbatimTextOutput("summaryTable"))
        
      )
    ),
    tabPanel("Traffic Concepts",
     sidebarLayout(
       sidebarPanel(
         h4('Select start date, end date, and concept'),
         dateInput("StartDateConcept", "Start Date:"),
         dateInput("EndtDateConcept", "End Date:"),
         checkboxGroupInput(
           "trafficConcepts", "Traffic Concepts",
           c(
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
           )
         ),
         actionButton("plotTLTC", "Plot Timelines"),
         checkboxInput("summaryTC", label = "Show Traffic Concepts Summary Statistics", value = FALSE)
       ),
       mainPanel(
         #     verbatimTextOutput("start"),
         #     verbatimTextOutput("end"),
         #     verbatimTextOutput("vector"),
         #     verbatimTextOutput("button"),
         style = "background-color:Wheat;",
         h4('Traffic Concepts Service', align = "center"),
         h4("This service is used to visualize the volume of tweets that mention one or more traffic concepts across all mentioned 
UK roads per hour within a specified time window."), 
         h4("The page also shows basic statistics about the timeline of each selected concept"),
         plotOutput("newPlotTC"),
         verbatimTextOutput("summaryTableTC"))
       
       )
    ),
    tabPanel("Traffic Concepts - Road Level",
             sidebarLayout(
               sidebarPanel(
                 h4('Select start date, end date, and concept'),
                 dateInput("StartDateConceptRL", "Start Date:"),
                 dateInput("EndtDateConceptRL", "End Date:"),
                 selectInput("selectRoad", label = h6("Select Road"), 
                             choices = list("M1" = "M1", "M5" = "M5", "M6" = "M6", "M25" = "M25", "M40" = "M40",
                                            "M62" = "M62", "A1" = "A1", "A46" = "A46", "A45" = "A45", "A5" = "A5"), 
                             multiple=FALSE),
                 checkboxGroupInput(
                   "trafficConceptsRL", "Traffic Concepts",
                   c(
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
                   )
                 ),
                 actionButton("plotTLTCRL", "Plot Timelines"),
                 checkboxInput("summaryTCRL", label = "Show Traffic Concepts Summary Statistics", value = FALSE)
               ),
               mainPanel(
                 #     verbatimTextOutput("start"),
                 #     verbatimTextOutput("end"),
                 #     verbatimTextOutput("vector"),
                 #     verbatimTextOutput("button"),
                 style = "background-color:Azure;",
                 h4('Traffic Concepts - Road Level Service', align = "center"),
                 h4("This service is used to visualize the volume of tweets that mention one or more traffic concepts for a specific UK
road within a specified time window."), 
                 h4("The page also shows basic statistics about the timeline of each selected concept"),
                 plotOutput("newPlotTCRL"),
                 verbatimTextOutput("summaryTableTCRL"))
               
               )
    )
  )
))

server <- function(input, output) {
  #   output$start <- renderPrint({input$StartDate})
  #   output$end <- renderPrint({input$EndtDate})
  #   output$vector <- renderPrint({input$highwayCodes})
  #   output$button <- renderPrint({input$plotTL})

  observe({
    if (input$plotTL == 0 || length(input$highwayCodes) < 1)
      return()

    isolate({   
      timelineplot <-
        eventReactive(input$plotTL, {
          plotHighwayTimeLines(input$StartDate,input$EndtDate,input$highwayCodes)
        })
      if (class(timelineplot()) == "list") {
        output$newPlot <- renderPlot({
          print(timelineplot()[[1]])
        })
      }
      else {
        return()
      }
      
      out_summary <- reactive({input$summary})
      output$summaryTable <- renderPrint({
        if (out_summary() && class(timelineplot()) == "list") {
          var <- timelineplot()[[2]]
          summary(var)
        }
      })
    })
  })
  
  observe({
    if (input$plotTLTC == 0 || length(input$trafficConcepts) < 1)
      return()
    isolate({
      timelineplotTC <-
        eventReactive(input$plotTLTC, {
          plotTrafficTimeLines(input$StartDateConcept,input$EndtDateConcept,input$trafficConcepts)
        })
      if (class(timelineplotTC()) == "list") {
        output$newPlotTC <- renderPlot({
          print(timelineplotTC()[[1]])
        })
      }
      else {
        return()
      }
      
      out_summary_tc <- reactive({input$summaryTC})
      output$summaryTableTC <- renderPrint({
        if (out_summary_tc() && class(timelineplotTC()) == "list") {
          var <- timelineplotTC()[[2]]
          summary(var)
        }
      })
    })
  })
  
  observe({
    if (input$plotTLTCRL == 0 || length(input$trafficConceptsRL) < 1)
      return()
    isolate({
      timelineplotTCRL <-
        eventReactive(input$plotTLTCRL, {
          plotTrafficTimeLinesOneRoad(input$StartDateConceptRL,input$EndtDateConceptRL,input$trafficConceptsRL,input$selectRoad)
        })
      if (class(timelineplotTCRL()) == "list") {
        output$newPlotTCRL <- renderPlot({
          print(timelineplotTCRL()[[1]])
        })
      }
      else {
        return()
      }
      
      out_summary_tc_rl <- reactive({input$summaryTCRL})
      output$summaryTableTCRL <- renderPrint({
        if (out_summary_tc_rl() && class(timelineplotTCRL()) == "list") {
          var <- timelineplotTCRL()[[2]]
          summary(var)
        }
      })
    })
  })
}

shinyApp(ui = ui, server = server)