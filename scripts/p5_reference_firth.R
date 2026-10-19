# Independent numerical reference. Participant data arrive through stdin only.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)) .libPaths(c(args[1], .libPaths()))
suppressPackageStartupMessages(library(brglm2))
suppressPackageStartupMessages(library(jsonlite))
input <- fromJSON(file("stdin"), simplifyVector=FALSE)
out <- lapply(input$cases, function(case) {
  x <- do.call(rbind, lapply(case$x, unlist))
  y <- unlist(case$y)
  colnames(x) <- unlist(case$names)
  d <- data.frame(y=y, x[, -1, drop=FALSE], check.names=FALSE)
  # Start from the intercept-only rate, avoiding an ordinary-GLM separated start.
  fit <- glm(y ~ ., data=d, family=binomial("logit"), method=brglmFit,
             start=c(qlogis(mean(y)), rep(0, ncol(x)-1)),
             control=brglmControl(type="AS_mean", epsilon=1e-8, maxit=1000, slowit=0.25))
  list(label=case$label, beta=unname(coef(fit)), covariance=unname(vcov(fit)),
       converged=isTRUE(fit$converged), iterations=fit$iter)
})
cat(toJSON(list(package="brglm2", version=as.character(packageVersion("brglm2")),
                R=R.version.string, type="AS_mean", cases=out),
           digits=16, auto_unbox=TRUE, matrix="rowmajor"))
