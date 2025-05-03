-- Insert sample problems
INSERT INTO problems (latex_text, comments, latex_versions, solution, category) VALUES
('Find all solutions to the equation $x^2 - 4x + 4 = 0$.', 'Basic quadratic equation', ARRAY['Solve $x^2 - 4x + 4 = 0$.'], 'The solution is $x = 2$ (double root).', 'A'),
('Prove that for any positive integer $n$, the number $n^2 + n + 1$ is never divisible by $3$.', 'Number theory problem for beginners', ARRAY['Show that $n^2 + n + 1$ is not divisible by $3$ for any $n \in \mathbb{N}$.'], 'For any $n$, either $n \equiv 0 \pmod{3}$, $n \equiv 1 \pmod{3}$, or $n \equiv 2 \pmod{3}$. Checking each case: if $n \equiv 0 \pmod{3}$, then $n^2 + n + 1 \equiv 0 + 0 + 1 \equiv 1 \pmod{3}$. If $n \equiv 1 \pmod{3}$, then $n^2 + n + 1 \equiv 1 + 1 + 1 \equiv 0 \pmod{3}$. If $n \equiv 2 \pmod{3}$, then $n^2 + n + 1 \equiv 4 + 2 + 1 \equiv 1 \pmod{3}$. So in all cases, $n^2 + n + 1$ is not divisible by $3$.', 'N'),
('In a triangle $ABC$, if $AB = 5$, $BC = 7$ and $\angle ABC = 60^{\circ}$, find the length of $AC$.', 'Law of cosines application', ARRAY['Calculate $AC$ in triangle $ABC$ where $AB = 5$, $BC = 7$, $\angle B = 60^{\circ}$.'], 'Using the law of cosines: $AC^2 = AB^2 + BC^2 - 2 \cdot AB \cdot BC \cdot \cos(\angle ABC)$. Substituting the values: $AC^2 = 5^2 + 7^2 - 2 \cdot 5 \cdot 7 \cdot \cos(60^{\circ}) = 25 + 49 - 70 \cdot 0.5 = 74 - 35 = 39$. Therefore, $AC = \sqrt{39} \approx 6.24$ units.', 'G'),
('How many ways can 8 different books be arranged on a shelf?', 'Basic permutation problem', ARRAY['In how many different ways can we arrange 8 distinct books on a shelf?'], 'This is a permutation of 8 distinct objects, so the answer is $8! = 8 \cdot 7 \cdot 6 \cdot 5 \cdot 4 \cdot 3 \cdot 2 \cdot 1 = 40320$.', 'C'),
('Calculate the limit: $\lim_{x \to 0} \frac{\sin(3x)}{x}$.', 'Limit using known result', ARRAY['Evaluate $\lim_{x \to 0} \frac{\sin(3x)}{x}$.'], 'Using the known limit $\lim_{x \to 0} \frac{\sin(x)}{x} = 1$, we can rewrite: $\lim_{x \to 0} \frac{\sin(3x)}{x} = \lim_{x \to 0} \frac{\sin(3x)}{3x} \cdot 3 = 3 \cdot \lim_{x \to 0} \frac{\sin(3x)}{3x} = 3 \cdot 1 = 3$.', 'A');

-- Insert sample problemsets
INSERT INTO problemsets (title, type, part_of) VALUES
('Algebra Basics', 'practice', 'skola matematike'),
('Number Theory Fundamentals', 'lecture', 'skola matematike'),
('Geometry Problems', 'test', 'ljetni kamp'),
('Mixed Problems', 'practice', 'zimski kamp');

-- Create the associations between problems and problemsets
INSERT INTO problemset_problems (id_problem, id_problemset) VALUES
(1, 1), -- Quadratic equation in Algebra Basics
(5, 1), -- Limit problem in Algebra Basics
(2, 2), -- Number theory problem in Number Theory Fundamentals
(3, 3), -- Geometry problem in Geometry Problems
(4, 4), -- Combinatorics problem in Mixed Problems
(1, 4), -- Quadratic equation also in Mixed Problems
(3, 4); -- Geometry problem also in Mixed Problems