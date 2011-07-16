library(ggplot2)
args <- commandArgs(trailingOnly = T)
corpus <- read.csv(paste(args[1],".csv", sep=""))
fit <- cmdscale(corpus, k=2)
data <- as.data.frame(fit)
data$Category <- gsub("\\d+ ", "", rownames(data))
data$URLID <- gsub("(\\d+)?.*", "\\1", rownames(fit))

Category <- factor(gsub("\\d+ ", "", rownames(fit)))

png(paste(args[1],"-mds.png", sep=""), width=500, height=500, res=100)

p <- ggplot(data) +
    geom_point(data=subset(data, URLID != ""),
        aes(x=V1, y=V2, size=1.5, color=Category)) +
    geom_point(data=subset(data, URLID == ""),
        aes(x=V1, y=V2, size=7, shape=c(1), color=Category)) +
    scale_x_continuous("", breaks=NA) +
    scale_y_continuous("", breaks=NA) +
    opts(axis.text.x = theme_blank(), axis.title.x=theme_blank(),
        axis.text.y = theme_blank(), axis.title.y=theme_blank(),
        legend.position = "none")

p 
dev.off()

png(paste(args[1],"-mds-faceted.png", sep=""), width=500, height=500, res=100)
p + facet_wrap(~ Category)
dev.off()

