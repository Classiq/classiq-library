# Derivations

## Single-realization spectral-norm error of the Boolean oracle sketch

**Claim.** For one random data sample $\lambda = (x_1, \dots, x_M)$ with $x_t \sim \mathrm{Unif}([N])$ and $\tau = \pi N$,

$$\|V_\lambda - O\|_2 \;=\; \mathcal{O}\!\bigl(\sqrt{N/M}\bigr) \cdot \mathcal{O}\!\bigl(\sqrt{\log N}\bigr).$$

### Step 1 — Error reduces to a max over diagonal entries

Both $V_\lambda$ and $O$ are diagonal in the computational basis (eq. 2 of the notebook):

$$V_\lambda - O \;=\; \sum_x \bigl[e^{i\pi N m_x f(x)} - e^{i\pi f(x)}\bigr]\,|x\rangle\!\langle x|.$$

The spectral norm of a diagonal matrix is the max absolute diagonal entry, so

$$\|V_\lambda - O\|_2 \;=\; \max_x |d_x|, \qquad d_x := e^{i\pi N m_x f(x)} - e^{i\pi f(x)}.$$

### Step 2 — Only the active bins contribute

If $f(x) = 0$ both phases equal $1$, so $d_x = 0$. From here on assume $f(x) = 1$.

### Step 3 — Linearise around the mean

Let $\delta_x := m_x - 1/N$ be the deviation of the empirical frequency from the true probability. Then

$$\pi N m_x \;=\; \pi N\bigl(1/N + \delta_x\bigr) \;=\; \pi + \pi N \delta_x,$$

so $e^{i\pi N m_x} = -\,e^{i\pi N \delta_x}$ and

$$d_x \;=\; -e^{i\pi N \delta_x} - (-1) \;=\; 1 - e^{i\pi N \delta_x}, \qquad |d_x| \;=\; 2\bigl|\sin(\pi N \delta_x / 2)\bigr| \;\approx\; \pi N \, |\delta_x|$$

for small $\delta_x$. In words: each diagonal error is $\pi N$ times the deviation of $m_x$ from $1/N$.

### Step 4 — Size of $\delta_x$

$M m_x$ is $\mathrm{Binomial}(M, 1/N)$, so

$$\operatorname{Var}(m_x) \;=\; \frac{1}{NM}\bigl(1 - 1/N\bigr) \;\approx\; \frac{1}{NM} \quad\Longrightarrow\quad |\delta_x| \;\sim\; \frac{1}{\sqrt{NM}}.$$

Substituting into Step 3:

$$|d_x| \;\sim\; \pi N \cdot \frac{1}{\sqrt{NM}} \;=\; \pi\,\sqrt{N/M}.$$

That's the typical _per-entry_ error.

### Step 5 — Max over $\sim N$ bins

The spectral norm is the largest $|d_x|$, not a typical one. About $N/2$ entries are active ($f(x) = 1$). The maximum of $\sim N$ approximately-Gaussian quantities each with standard deviation $\sigma$ is $\sigma\sqrt{2\log N}$, contributing the extra $\sqrt{\log N}$ factor:

$$\|V_\lambda - O\|_2 \;=\; \mathcal{O}\!\bigl(\sqrt{N/M}\bigr) \cdot \mathcal{O}\!\bigl(\sqrt{\log N}\bigr).$$

### Intuition

The choice $\tau = \pi N$ amplifies any deviation of $m_x$ from its mean by a factor of $\pi N$. The CLT gives $|\delta_x| \sim 1/\sqrt{NM}$. The product is $\sqrt{N/M}$. Larger $N$ → noisier empirical estimates per bin (each bin sees only $\sim M/N$ samples), partially offset by the $1/\sqrt{N}$ inside the variance.

---

## Why the channel error is $N/M$ instead of $\sqrt{N/M}$

The single-realization $|d_x|$ has zero mean but standard deviation $\sim \sqrt{N/M}$. When we _average_ $V_\lambda$ over $\lambda$, the noisy $\pm$ deviations cancel and only the **bias** survives. The bias is second-order:

$$\mathbb{E}\!\left[e^{i\pi N m_x}\right] \;=\; \bigl(1 - 1/N + e^{i\pi N/M}/N\bigr)^M.$$

Expanding $e^{i\pi N/M} \approx 1 + i\pi N/M - \tfrac{(\pi N)^2}{2M^2}$ and keeping leading terms gives

$$\mathbb{E}\!\left[e^{i\pi N m_x}\right] \;\approx\; \exp\!\Bigl(i\pi - \tfrac{\pi^2 N}{2M}\Bigr) \;=\; -\,e^{-\pi^2 N/(2M)} \;\approx\; -1 + \frac{\pi^2 N}{2M}.$$

The difference from $e^{i\pi} = -1$ is $\pi^2 N/(2M)$, so

$$\bigl\|\mathbb{E}[V_\lambda] - O\bigr\| \;\sim\; N/M.$$

For large $M$ we have $N/M \ll \sqrt{N/M}$, which is why the channel curve drops below the single-realization curve in the plot: a single noisy realisation is dominated by _variance_, whereas the channel (a unitary average over runs) is dominated by _bias_, and the bias is quadratically smaller.
