# From average coordination effects to forecastable risk states

## Different estimands

Let S be the full source state, X the allowed macro history, Y the next-hour realized risk, and m(S)=E[Y|S]. The model-conditional intervention contrast

\[
\Delta(S)=E[Y^{\mathrm{common}}-Y^{\mathrm{independent}}\mid S]
\]

can have positive population mean without providing additional information about variation in m within the common-signal world. A nearly constant risk increment is absorbed into that world's baseline level. A varying increment may be redundant with activity, or unobservable from X. These are distinct from noisy estimation of Delta.

For positive Y and forecasts p, QLIKE is L(Y,p)=Y/p−log(Y/p)−1. With finite expectations and positive conditional means m_X=E[Y|X], m_XZ=E[Y|X,Z],

\[
E[L(Y,m_X)-L(Y,m_{XZ})]
=E[\log(m_X)-\log(m_{XZ})]\ge0.
\]

The identity follows by conditional averaging and E[m_XZ/m_X]=1. It concerns the exact conditional means; a fitted learner can perform worse through estimation error. A positive cross-world mean Delta is not this within-world conditional forecasting gain. Failure of finite learners is not a proof that X contains no information.

## Same-law precision repair

The inherited bar price equation is

\[
r_j=\alpha+\beta Y_j+\sigma\sqrt{g_j^2}\,\epsilon_j,
\qquad g_j^2=V_j/\bar V_{\rm fit},
\]

where Y_j is realized impact minus predictable-impact recovery, formed before the current independent price shock. Therefore

\[
E[r_j^2\mid\mathcal F_j^{\rm pre-price}]
=(\alpha+\beta Y_j)^2+\sigma^2 g_j^2.
\]

The tower property makes the sum of these barwise conditional moments an unbiased simulation label for forward expected RV. Actual r_j, including its price shock, is still fed into subsequent trading feedback. Dropping those shocks from the state trajectory would change the model.

Because later Y depends on earlier price shocks, this termwise integration is not a global Rao–Blackwell projection of the full sum on one conditioning sigma-algebra. Variance reduction is measured, not assumed. It removes current-bar squared-noise and cross-term variation while preserving the stochastic law.

## Decomposing true heterogeneity and Monte Carlo error

For independent future replicates A and B at each origin, conditional on S,

\[
\operatorname{Cov}_{S,A,B}(\widehat m_A,\widehat m_B)
=\operatorname{Var}_S[m(S)].
\]

The same identity applies to paired-arm Delta estimates when future streams A/B are independent. Signed estimates of this covariance remain untruncated. A negative finite estimate signals insufficient precision to establish positive heterogeneity; it is not a negative physical variance. Replicate differences estimate Monte Carlo noise separately from between-state variation.

Activity-adjusted comparisons must fit the activity predictor outside the evaluated origins and use separate future replicates for Delta labels and risk outcomes. Otherwise label noise can mechanically create apparent risk information.

## Observable repair candidate: persistence, innovation and impact

The network already contains persistent directions, nonlinear impact and recovery of predictable pressure. A macro approximation can distinguish

\[
p_t=F_t/V_t=\widehat p_{t|t-1}+u_t,
\qquad
r_t\approx\alpha+\lambda[p_t-\chi\widehat p_{t|t-1}]+e_t.
\]

Predictable pressure and pressure innovations enter risk differently when recovery chi is nonzero. The proposed effective state is the combination of pressure persistence, pressure-innovation variance and observed impact/residual scale; it is not a measured coordinating-investor count. A finite past-only linear state approximation can propagate these moments to the same one-hour risk target, with its approximation error evaluated against market data and shared-information controls.

This direction is consistent with the distinction between persistent order flow and compensating price/liquidity response in [Bouchaud et al., Quantitative Finance4(2004),176–190](https://doi.org/10.1088/1469-7688/4/2/007), [Lillo and Farmer, The long memory of the efficient market](https://arxiv.org/abs/cond-mat/0311053), and [Bouchaud, Kockelkoren and Potters, liquidity molasses](https://arxiv.org/abs/cond-mat/0406224). Those studies motivate the distinction; they do not validate this particular five-minute Bitcoin approximation or guarantee volatility-prediction gains.

## A cancellation identity discovered in acceptance

The finite H1 inner selection chose chi=1 for the observable closure. This does not identify the true market recovery coefficient. With constant local innovation moments, no volume forecast and no fallback, let u be pressure innovation, e=r−alpha−lambda*u, v=mean20(u²), eta=mean20(u*e)/v and z=e−eta*u. The construction gives mean20(u*z)=0. Thus

\[
(\lambda+\eta)^2 v+\operatorname{mean}_{20}(z^2)
=\operatorname{mean}_{20}[(r-\alpha)^2].
\]

Complete recovery cancels pressure predictability from each future mean return in this closure. At h=12,

\[
\widehat R_{12}^{\rm local}
=12\{\alpha^2+\operatorname{mean}_{20}[(r-\alpha)^2]\}.
\]

This equality was independently checked on all3801training and674query histories. The forecast therefore contains a return-second-moment identity at this limit; apparent gains against a4/12/32bar HAR can reflect the added20bar summary. It is a diagnostic identity of this closure, not a theorem that coordination never predicts risk. Separate prediction of volume-scaled noise and decomposition features can add modeling assumptions; their contributions require the explicit matched-representation controls.
