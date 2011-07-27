library(ggplot2)
args <- commandArgs(trailingOnly = T)
directory <- args[1]
corpus <- read.csv(paste(directory,"/corpus.csv", sep=""))
fit <- cmdscale(corpus, k=2)
data <- as.data.frame(fit)
data$Category <- gsub("\\d+ ", "", rownames(data))

Category <- factor(gsub("\\d+ ", "", rownames(fit)))

png(paste(directory,"/corpus-mds.png", sep=""), width=500, height=500, res=100)

p <- ggplot(data) +
    geom_point(aes(x=V1, y=V2, color=Category)) +
    scale_x_continuous("", breaks=NA) +
    scale_y_continuous("", breaks=NA) +
    opts(axis.text.x = theme_blank(), axis.title.x=theme_blank(),
        axis.text.y = theme_blank(), axis.title.y=theme_blank(),
        legend.position = "none")
p 
dev.off()

corpus <- read.csv(paste(directory,"/models.csv", sep=""))
fit <- cmdscale(corpus, k=2)
data <- as.data.frame(fit)
data$Category <- rownames(data)
png(paste(directory,"/corpus-mds-centroids.png", sep=""),
    width=500, height=500, res=100)
p <- ggplot(data) +
    geom_text(aes(x=V1, y=V2, label=Category, size=3, color=Category)) +
    scale_x_continuous("", breaks=NA) +
    scale_y_continuous("", breaks=NA) +
    opts(axis.text.x = theme_blank(), axis.title.x=theme_blank(),
        axis.text.y = theme_blank(), axis.title.y=theme_blank(),
        legend.position = "none")
p
dev.off()

png(paste(directory,"/corpus-mds-faceted.png", sep=""),
    width=500, height=500, res=100)
p <- ggplot(data)
cats <- as.vector(unique(Category))
for(cat in cats)
{
    corpus <- read.csv(paste(directory,"/",cat,".csv", sep=""))
    if(nrow(corpus) > 2)
    {
        fit <- cmdscale(corpus, k=2)
        data_cat <- as.data.frame(fit)
        data_cat$Category <- gsub("\\d+ ", "", rownames(data_cat))
        data_cat$URLID <- gsub("(\\d+)?.*", "\\1", rownames(fit))

        p <- p + geom_point(data=subset(data_cat, URLID != ""),
                aes(x=V1, y=V2, size=1.5, color=Category)) +
            geom_point(data=subset(data_cat, URLID == ""),
                aes(x=V1, y=V2, size=7, shape=c(1)))
    }
}
p <- p + scale_x_continuous("", breaks=NA) +
    scale_y_continuous("", breaks=NA) +
    opts(axis.text.x = theme_blank(), axis.title.x=theme_blank(),
        axis.text.y = theme_blank(), axis.title.y=theme_blank(),
        legend.position = "none") +
    facet_wrap(~ Category)
p
dev.off()

