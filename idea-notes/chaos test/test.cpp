/*
 * ================================================================
 *
 *                       CHAOS LABORATORY
 *
 *
 *
 * ================================================================
 *
 * A single-file nonlinear dynamics laboratory.
 *
 * Systems:
 *
 *   1. Logistic Map
 *   2. Lorenz Attractor
 *   3. Rössler Attractor
 *   4. Hénon Map
 *   5. Ikeda Map
 *   6. Duffing Oscillator
 *   7. Double Pendulum
 *
 * Numerical methods:
 *
 *   - Euler
 *   - Classical fourth-order Runge-Kutta
 *
 * Analysis:
 *
 *   - Trajectory generation
 *   - Largest Lyapunov exponent estimate
 *   - Initial-condition sensitivity
 *   - Logistic bifurcation diagram
 *   - Poincaré section
 *   - Basic statistics
 *
 * Output:
 *
 *   - ASCII plots
 *   - CSV
 *   - PPM images
 *
 * Build:
 *
 *   gcc -std=c99 -O2 chaos.c -lm -o chaos
 *
 * ================================================================
 */

#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>
#include <stdbool.h>
#include <float.h>
#include <errno.h>

#ifndef M_PI
#define M_PI 3.141592653589793238462643383279502884
#endif

#define VERSION "1.0"

#define MAX_STATE 8
#define INITIAL_CAPACITY 4096
#define INPUT_SIZE 512

#define DEFAULT_ASCII_WIDTH 100
#define DEFAULT_ASCII_HEIGHT 36

#define DEFAULT_IMAGE_WIDTH 1200
#define DEFAULT_IMAGE_HEIGHT 900

#define EPSILON_DEFAULT 1e-8


 /* ================================================================
  * Basic data structures
  * ================================================================ */

typedef struct
{
    double v[MAX_STATE];
    int n;
} State;


typedef struct
{
    double t0;
    double dt;
    int steps;
} SimulationConfig;


typedef struct
{
    State* data;

    size_t count;
    size_t capacity;

} Trajectory;


typedef struct
{
    unsigned char r;
    unsigned char g;
    unsigned char b;

} Pixel;


typedef struct
{
    int width;
    int height;

    Pixel* data;

} Image;


typedef struct
{
    double min_x;
    double max_x;

    double min_y;
    double max_y;

} Bounds;


/*
 * Derivative callback for continuous dynamical systems.
 */
typedef void (*DerivativeFunction)(
    double t,
    const State* state,
    State* derivative,
    void* parameters
    );


/*
 * Iteration callback for discrete maps.
 */
typedef void (*MapFunction)(
    const State* state,
    State* next,
    void* parameters
    );


/*
 * Generic dynamical system descriptor.
 */
typedef struct
{
    const char* name;

    int dimension;

    DerivativeFunction derivative;

    MapFunction map;

    void* parameters;

} DynamicalSystem;


/* ================================================================
 * Utility functions
 * ================================================================ */

static void fatal_error(const char* message)
{
    fprintf(stderr, "\nFATAL ERROR: %s\n", message);
    exit(EXIT_FAILURE);
}


static void* xmalloc(size_t size)
{
    void* ptr = malloc(size);

    if (!ptr)
        fatal_error("Memory allocation failed.");

    return ptr;
}


static void* xcalloc(size_t count, size_t size)
{
    void* ptr = calloc(count, size);

    if (!ptr)
        fatal_error("Memory allocation failed.");

    return ptr;
}


static void* xrealloc(void* ptr, size_t size)
{
    void* new_ptr = realloc(ptr, size);

    if (!new_ptr)
        fatal_error("Memory reallocation failed.");

    return new_ptr;
}


static double clamp_double(
    double x,
    double minimum,
    double maximum
)
{
    if (x < minimum)
        return minimum;

    if (x > maximum)
        return maximum;

    return x;
}


static void state_zero(State* state, int dimension)
{
    int i;

    state->n = dimension;

    for (i = 0; i < dimension; ++i)
        state->v[i] = 0.0;
}


static void state_copy(
    State* destination,
    const State* source
)
{
    int i;

    destination->n = source->n;

    for (i = 0; i < source->n; ++i)
        destination->v[i] = source->v[i];
}


static double state_distance(
    const State* a,
    const State* b
)
{
    double sum = 0.0;

    int dimension = a->n < b->n
        ? a->n
        : b->n;

    int i;

    for (i = 0; i < dimension; ++i)
    {
        double difference =
            a->v[i] - b->v[i];

        sum += difference * difference;
    }

    return sqrt(sum);
}


static void state_add_scaled(
    State* output,
    const State* a,
    const State* b,
    double scale
)
{
    int i;

    output->n = a->n;

    for (i = 0; i < a->n; ++i)
    {
        output->v[i] =
            a->v[i] +
            b->v[i] * scale;
    }
}


/* ================================================================
 * Input helpers
 * ================================================================ */

static void trim_newline(char* text)
{
    size_t length = strlen(text);

    while (
        length > 0 &&
        (
            text[length - 1] == '\n' ||
            text[length - 1] == '\r'
            )
        )
    {
        text[length - 1] = '\0';
        --length;
    }
}


static void read_line(
    char* buffer,
    size_t size
)
{
    if (!fgets(buffer, (int)size, stdin))
    {
        clearerr(stdin);
        buffer[0] = '\0';
        return;
    }

    trim_newline(buffer);
}


static int ask_int(
    const char* prompt,
    int minimum,
    int maximum,
    int default_value
)
{
    char buffer[INPUT_SIZE];

    for (;;)
    {
        char* end;
        long value;

        printf(
            "%s [%d]: ",
            prompt,
            default_value
        );

        fflush(stdout);

        read_line(buffer, sizeof(buffer));

        if (buffer[0] == '\0')
            return default_value;

        errno = 0;

        value = strtol(
            buffer,
            &end,
            10
        );

        if (
            errno == 0 &&
            end != buffer &&
            *end == '\0' &&
            value >= minimum &&
            value <= maximum
            )
        {
            return (int)value;
        }

        printf(
            "Enter an integer between %d and %d.\n",
            minimum,
            maximum
        );
    }
}


static double ask_double(
    const char* prompt,
    double minimum,
    double maximum,
    double default_value
)
{
    char buffer[INPUT_SIZE];

    for (;;)
    {
        char* end;
        double value;

        printf(
            "%s [%.10g]: ",
            prompt,
            default_value
        );

        fflush(stdout);

        read_line(buffer, sizeof(buffer));

        if (buffer[0] == '\0')
            return default_value;

        errno = 0;

        value = strtod(
            buffer,
            &end
        );

        if (
            errno == 0 &&
            end != buffer &&
            *end == '\0' &&
            isfinite(value) &&
            value >= minimum &&
            value <= maximum
            )
        {
            return value;
        }

        printf(
            "Enter a number between %.10g and %.10g.\n",
            minimum,
            maximum
        );
    }
}


static void pause_screen(void)
{
    char buffer[INPUT_SIZE];

    printf("\nPress ENTER to continue...");
    fflush(stdout);

    read_line(buffer, sizeof(buffer));
}


/* ================================================================
 * State printing
 * ================================================================ */

static void print_state(const State* state)
{
    int i;

    printf("(");

    for (i = 0; i < state->n; ++i)
    {
        printf(
            "%.10g",
            state->v[i]
        );

        if (i + 1 < state->n)
            printf(", ");
    }

    printf(")");
}


/* ================================================================
 * Trajectory management
 * ================================================================ */

static Trajectory* trajectory_create(
    size_t initial_capacity
)
{
    Trajectory* trajectory;

    trajectory =
        (Trajectory*)xmalloc(
            sizeof(Trajectory)
        );

    trajectory->data =
        (State*)xmalloc(
            sizeof(State) * initial_capacity
        );

    trajectory->count = 0;
    trajectory->capacity = initial_capacity;

    return trajectory;
}


static void trajectory_destroy(
    Trajectory* trajectory
)
{
    if (!trajectory)
        return;

    free(trajectory->data);
    free(trajectory);
}


static void trajectory_clear(
    Trajectory* trajectory
)
{
    trajectory->count = 0;
}


static void trajectory_push(
    Trajectory* trajectory,
    const State* state
)
{
    if (
        trajectory->count >=
        trajectory->capacity
        )
    {
        size_t new_capacity =
            trajectory->capacity * 2;

        trajectory->data =
            (State*)xrealloc(
                trajectory->data,
                sizeof(State) * new_capacity
            );

        trajectory->capacity =
            new_capacity;
    }

    state_copy(
        &trajectory->data[
            trajectory->count
        ],
        state
    );

    ++trajectory->count;
}


/* ================================================================
 * Image management
 * ================================================================ */

static Image* image_create(
    int width,
    int height
)
{
    Image* image;

    image =
        (Image*)xmalloc(
            sizeof(Image)
        );

    image->width = width;
    image->height = height;

    image->data =
        (Pixel*)xcalloc(
            (size_t)width *
            (size_t)height,
            sizeof(Pixel)
        );

    return image;
}


static void image_destroy(
    Image* image
)
{
    if (!image)
        return;

    free(image->data);
    free(image);
}


static void image_clear(
    Image* image,
    Pixel color
)
{
    size_t count =
        (size_t)image->width *
        (size_t)image->height;

    size_t i;

    for (i = 0; i < count; ++i)
        image->data[i] = color;
}


static void image_set_pixel(
    Image* image,
    int x,
    int y,
    Pixel color
)
{
    if (
        x < 0 ||
        x >= image->width ||
        y < 0 ||
        y >= image->height
        )
    {
        return;
    }

    image->data[
        (size_t)y *
            (size_t)image->width +
            (size_t)x
    ] = color;
}


static void image_add_pixel(
    Image* image,
    int x,
    int y,
    Pixel color
)
{
    Pixel* pixel;

    if (
        x < 0 ||
        x >= image->width ||
        y < 0 ||
        y >= image->height
        )
    {
        return;
    }

    pixel =
        &image->data[
            (size_t)y *
                (size_t)image->width +
                (size_t)x
        ];

    if (color.r > pixel->r)
        pixel->r = color.r;

    if (color.g > pixel->g)
        pixel->g = color.g;

    if (color.b > pixel->b)
        pixel->b = color.b;
}


static int image_write_ppm(
    const Image* image,
    const char* filename
)
{
    FILE* file;
    int x;
    int y;

    file = fopen(filename, "wb");

    if (!file)
        return 0;

    fprintf(
        file,
        "P6\n%d %d\n255\n",
        image->width,
        image->height
    );

    for (y = 0; y < image->height; ++y)
    {
        for (x = 0; x < image->width; ++x)
        {
            const Pixel* pixel =
                &image->data[
                    (size_t)y *
                        (size_t)image->width +
                        (size_t)x
                ];

            fputc(pixel->r, file);
            fputc(pixel->g, file);
            fputc(pixel->b, file);
        }
    }

    fclose(file);

    return 1;
}


/* ================================================================
 * Numerical integration
 * ================================================================ */

static void euler_step(
    DerivativeFunction function,
    double time,
    double dt,
    const State* state,
    State* output,
    void* parameters
)
{
    State derivative;
    int i;

    function(
        time,
        state,
        &derivative,
        parameters
    );

    output->n = state->n;

    for (i = 0; i < state->n; ++i)
    {
        output->v[i] =
            state->v[i] +
            dt * derivative.v[i];
    }
}


static void rk4_step(
    DerivativeFunction function,
    double time,
    double dt,
    const State* state,
    State* output,
    void* parameters
)
{
    State k1;
    State k2;
    State k3;
    State k4;

    State temp;

    int i;

    function(
        time,
        state,
        &k1,
        parameters
    );

    state_add_scaled(
        &temp,
        state,
        &k1,
        dt * 0.5
    );

    function(
        time + dt * 0.5,
        &temp,
        &k2,
        parameters
    );

    state_add_scaled(
        &temp,
        state,
        &k2,
        dt * 0.5
    );

    function(
        time + dt * 0.5,
        &temp,
        &k3,
        parameters
    );

    state_add_scaled(
        &temp,
        state,
        &k3,
        dt
    );

    function(
        time + dt,
        &temp,
        &k4,
        parameters
    );

    output->n = state->n;

    for (i = 0; i < state->n; ++i)
    {
        output->v[i] =
            state->v[i] +
            dt / 6.0 *
            (
                k1.v[i] +
                2.0 * k2.v[i] +
                2.0 * k3.v[i] +
                k4.v[i]
                );
    }
}


/* ================================================================
 * Generic simulation
 * ================================================================ */

static void integrate_system(
    const DynamicalSystem* system,
    const State* initial,
    const SimulationConfig* config,
    int method,
    Trajectory* trajectory
)
{
    State current;
    State next;

    int i;

    state_copy(
        &current,
        initial
    );

    trajectory_clear(trajectory);

    trajectory_push(
        trajectory,
        &current
    );

    for (i = 0; i < config->steps; ++i)
    {
        double time =
            config->t0 +
            (double)i * config->dt;

        if (method == 0)
        {
            euler_step(
                system->derivative,
                time,
                config->dt,
                &current,
                &next,
                system->parameters
            );
        }
        else
        {
            rk4_step(
                system->derivative,
                time,
                config->dt,
                &current,
                &next,
                system->parameters
            );
        }

        state_copy(
            &current,
            &next
        );

        if (!isfinite(current.v[0]))
            break;

        trajectory_push(
            trajectory,
            &current
        );
    }
}


static void iterate_map(
    const DynamicalSystem* system,
    const State* initial,
    int steps,
    Trajectory* trajectory
)
{
    State current;
    State next;

    int i;

    state_copy(
        &current,
        initial
    );

    trajectory_clear(trajectory);

    trajectory_push(
        trajectory,
        &current
    );

    for (i = 0; i < steps; ++i)
    {
        system->map(
            &current,
            &next,
            system->parameters
        );

        state_copy(
            &current,
            &next
        );

        if (!isfinite(current.v[0]))
            break;

        trajectory_push(
            trajectory,
            &current
        );
    }
}


/* ================================================================
 * 1. Logistic Map
 *
 * x(n+1) = r*x(n)*(1-x(n))
 * ================================================================ */

typedef struct
{
    double r;

} LogisticParameters;


static void logistic_map(
    const State* state,
    State* next,
    void* parameters
)
{
    LogisticParameters* p =
        (LogisticParameters*)parameters;

    double x = state->v[0];

    next->n = 1;

    next->v[0] =
        p->r *
        x *
        (1.0 - x);
}


/* ================================================================
 * 2. Lorenz System
 *
 * dx/dt = sigma(y-x)
 * dy/dt = x(rho-z)-y
 * dz/dt = xy-beta*z
 * ================================================================ */

typedef struct
{
    double sigma;
    double rho;
    double beta;

} LorenzParameters;


static void lorenz_derivative(
    double time,
    const State* state,
    State* derivative,
    void* parameters
)
{
    LorenzParameters* p =
        (LorenzParameters*)parameters;

    double x = state->v[0];
    double y = state->v[1];
    double z = state->v[2];

    (void)time;

    derivative->n = 3;

    derivative->v[0] =
        p->sigma *
        (y - x);

    derivative->v[1] =
        x *
        (p->rho - z)
        - y;

    derivative->v[2] =
        x * y
        - p->beta * z;
}


/* ================================================================
 * 3. Rössler System
 *
 * dx/dt = -y-z
 * dy/dt = x+a*y
 * dz/dt = b+z(x-c)
 * ================================================================ */

typedef struct
{
    double a;
    double b;
    double c;

} RosslerParameters;


static void rossler_derivative(
    double time,
    const State* state,
    State* derivative,
    void* parameters
)
{
    RosslerParameters* p =
        (RosslerParameters*)parameters;

    double x = state->v[0];
    double y = state->v[1];
    double z = state->v[2];

    (void)time;

    derivative->n = 3;

    derivative->v[0] =
        -y - z;

    derivative->v[1] =
        x + p->a * y;

    derivative->v[2] =
        p->b +
        z * (x - p->c);
}


/* ================================================================
 * 4. Hénon Map
 *
 * x(n+1) = 1-a*x^2+y
 * y(n+1) = b*x
 * ================================================================ */

typedef struct
{
    double a;
    double b;

} HenonParameters;


static void henon_map(
    const State* state,
    State* next,
    void* parameters
)
{
    HenonParameters* p =
        (HenonParameters*)parameters;

    double x = state->v[0];
    double y = state->v[1];

    next->n = 2;

    next->v[0] =
        1.0 -
        p->a * x * x +
        y;

    next->v[1] =
        p->b * x;
}


/* ================================================================
 * 5. Ikeda Map
 * ================================================================ */

typedef struct
{
    double u;

} IkedaParameters;


static void ikeda_map(
    const State* state,
    State* next,
    void* parameters
)
{
    IkedaParameters* p =
        (IkedaParameters*)parameters;

    double x = state->v[0];
    double y = state->v[1];

    double tau =
        0.4 -
        6.0 /
        (
            1.0 +
            x * x +
            y * y
            );

    double c = cos(tau);
    double s = sin(tau);

    next->n = 2;

    next->v[0] =
        1.0 +
        p->u *
        (
            x * c -
            y * s
            );

    next->v[1] =
        p->u *
        (
            x * s +
            y * c
            );
}


/* ================================================================
 * 6. Duffing Oscillator
 *
 * x'' + delta*x'
 *      + alpha*x
 *      + beta*x^3
 *      = gamma*cos(omega*t)
 *
 * State:
 *
 * x
 * v
 * ================================================================ */

typedef struct
{
    double delta;
    double alpha;
    double beta;
    double gamma;
    double omega;

} DuffingParameters;


static void duffing_derivative(
    double time,
    const State* state,
    State* derivative,
    void* parameters
)
{
    DuffingParameters* p =
        (DuffingParameters*)parameters;

    double x = state->v[0];
    double velocity = state->v[1];

    derivative->n = 2;

    derivative->v[0] =
        velocity;

    derivative->v[1] =
        -p->delta * velocity
        - p->alpha * x
        - p->beta * x * x * x
        + p->gamma *
        cos(p->omega * time);
}


/* ================================================================
 * 7. Double Pendulum
 * ================================================================ */

typedef struct
{
    double m1;
    double m2;

    double l1;
    double l2;

    double g;

} PendulumParameters;


static void double_pendulum_derivative(
    double time,
    const State* state,
    State* derivative,
    void* parameters
)
{
    PendulumParameters* p =
        (PendulumParameters*)parameters;

    double theta1 = state->v[0];
    double omega1 = state->v[1];

    double theta2 = state->v[2];
    double omega2 = state->v[3];

    double delta =
        theta2 - theta1;

    double denominator1 =
        p->l1 *
        (
            2.0 * p->m1 +
            p->m2 -
            p->m2 *
            cos(
                2.0 * theta1 -
                2.0 * theta2
            )
            );

    double denominator2 =
        p->l2 *
        (
            2.0 * p->m1 +
            p->m2 -
            p->m2 *
            cos(
                2.0 * theta1 -
                2.0 * theta2
            )
            );

    double acceleration1 =
        (
            -p->g *
            (2.0 * p->m1 + p->m2) *
            sin(theta1)

            - p->m2 *
            p->g *
            sin(
                theta1 -
                2.0 * theta2
            )

            - 2.0 *
            sin(delta) *
            p->m2 *
            (
                omega2 * omega2 * p->l2
                +
                omega1 * omega1 *
                p->l1 *
                cos(delta)
                )
            )
        /
        denominator1;

    double acceleration2 =
        (
            2.0 *
            sin(delta) *
            (
                omega1 * omega1 *
                p->l1 *
                (p->m1 + p->m2)

                +
                p->g *
                (p->m1 + p->m2) *
                cos(theta1)

                +
                omega2 * omega2 *
                p->l2 *
                p->m2 *
                cos(delta)
                )
            )
        /
        denominator2;

    (void)time;

    derivative->n = 4;

    derivative->v[0] =
        omega1;

    derivative->v[1] =
        acceleration1;

    derivative->v[2] =
        omega2;

    derivative->v[3] =
        acceleration2;
}


/* ================================================================
 * System constructors
 * ================================================================ */

static DynamicalSystem make_logistic(
    LogisticParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Logistic Map";
    system.dimension = 1;
    system.derivative = NULL;
    system.map = logistic_map;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_lorenz(
    LorenzParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Lorenz Attractor";
    system.dimension = 3;
    system.derivative = lorenz_derivative;
    system.map = NULL;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_rossler(
    RosslerParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Rössler Attractor";
    system.dimension = 3;
    system.derivative = rossler_derivative;
    system.map = NULL;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_henon(
    HenonParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Hénon Map";
    system.dimension = 2;
    system.derivative = NULL;
    system.map = henon_map;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_ikeda(
    IkedaParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Ikeda Map";
    system.dimension = 2;
    system.derivative = NULL;
    system.map = ikeda_map;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_duffing(
    DuffingParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Duffing Oscillator";
    system.dimension = 2;
    system.derivative = duffing_derivative;
    system.map = NULL;
    system.parameters = parameters;

    return system;
}


static DynamicalSystem make_pendulum(
    PendulumParameters* parameters
)
{
    DynamicalSystem system;

    system.name = "Double Pendulum";
    system.dimension = 4;
    system.derivative =
        double_pendulum_derivative;

    system.map = NULL;

    system.parameters =
        parameters;

    return system;
}


/* ================================================================
 * Bounds
 * ================================================================ */

static Bounds trajectory_bounds(
    const Trajectory* trajectory,
    int x_index,
    int y_index
)
{
    Bounds bounds;

    size_t i;

    bounds.min_x = DBL_MAX;
    bounds.max_x = -DBL_MAX;

    bounds.min_y = DBL_MAX;
    bounds.max_y = -DBL_MAX;

    for (i = 0; i < trajectory->count; ++i)
    {
        double x =
            trajectory->data[i].v[x_index];

        double y =
            trajectory->data[i].v[y_index];

        if (
            !isfinite(x) ||
            !isfinite(y)
            )
        {
            continue;
        }

        if (x < bounds.min_x)
            bounds.min_x = x;

        if (x > bounds.max_x)
            bounds.max_x = x;

        if (y < bounds.min_y)
            bounds.min_y = y;

        if (y > bounds.max_y)
            bounds.max_y = y;
    }

    if (
        bounds.min_x == DBL_MAX
        )
    {
        bounds.min_x = -1.0;
        bounds.max_x = 1.0;

        bounds.min_y = -1.0;
        bounds.max_y = 1.0;
    }

    if (
        fabs(
            bounds.max_x -
            bounds.min_x
        ) < 1e-15
        )
    {
        bounds.min_x -= 1.0;
        bounds.max_x += 1.0;
    }

    if (
        fabs(
            bounds.max_y -
            bounds.min_y
        ) < 1e-15
        )
    {
        bounds.min_y -= 1.0;
        bounds.max_y += 1.0;
    }

    return bounds;
}


/* ================================================================
 * ASCII visualization
 * ================================================================ */

static void ascii_plot(
    const Trajectory* trajectory,
    int x_index,
    int y_index,
    int width,
    int height,
    size_t skip
)
{
    char* canvas;

    Bounds bounds;

    size_t i;

    if (width < 20)
        width = 20;

    if (height < 10)
        height = 10;

    canvas =
        (char*)xmalloc(
            (size_t)width *
            (size_t)height
        );

    memset(
        canvas,
        ' ',
        (size_t)width *
        (size_t)height
    );

    bounds =
        trajectory_bounds(
            trajectory,
            x_index,
            y_index
        );

    if (skip >= trajectory->count)
        skip = 0;

    for (
        i = skip;
        i < trajectory->count;
        ++i
        )
    {
        double x =
            trajectory->data[i].v[x_index];

        double y =
            trajectory->data[i].v[y_index];

        int px;
        int py;

        if (
            !isfinite(x) ||
            !isfinite(y)
            )
        {
            continue;
        }

        px =
            (int)
            (
                (x - bounds.min_x) /
                (bounds.max_x - bounds.min_x) *
                (double)(width - 1)
                );

        py =
            (int)
            (
                (bounds.max_y - y) /
                (bounds.max_y - bounds.min_y) *
                (double)(height - 1)
                );

        if (
            px >= 0 &&
            px < width &&
            py >= 0 &&
            py < height
            )
        {
            char character = '.';

            if (i == trajectory->count - 1)
                character = '@';

            else if (
                canvas[
                    (size_t)py *
                        (size_t)width +
                        (size_t)px
                ] == '.'
                )
            {
                character = '*';
            }

            canvas[
                (size_t)py *
                    (size_t)width +
                    (size_t)px
            ] = character;
        }
    }

    printf("\n");

    for (int y = 0; y < height; ++y)
    {
        putchar('|');

        for (int x = 0; x < width; ++x)
        {
            putchar(
                canvas[
                    (size_t)y *
                        (size_t)width +
                        (size_t)x
                ]
            );
        }

        putchar('|');
        putchar('\n');
    }

    printf("+");

    for (i = 0; i < (size_t)width; ++i)
        putchar('-');

    printf("+\n");

    free(canvas);
}


/* ================================================================
 * Trajectory PPM renderer
 * ================================================================ */

static void render_trajectory_ppm(
    const Trajectory* trajectory,
    int x_index,
    int y_index,
    const char* filename,
    int width,
    int height,
    size_t skip
)
{
    Image* image;

    Bounds bounds;

    Pixel background =
    { 5, 5, 8 };

    Pixel trail =
    { 80, 210, 255 };

    Pixel head =
    { 255, 255, 255 };

    size_t i;

    image =
        image_create(
            width,
            height
        );

    image_clear(
        image,
        background
    );

    bounds =
        trajectory_bounds(
            trajectory,
            x_index,
            y_index
        );

    for (
        i = skip;
        i < trajectory->count;
        ++i
        )
    {
        double x =
            trajectory->data[i].v[x_index];

        double y =
            trajectory->data[i].v[y_index];

        int px;
        int py;

        if (
            !isfinite(x) ||
            !isfinite(y)
            )
        {
            continue;
        }

        px =
            (int)
            (
                (x - bounds.min_x) /
                (bounds.max_x - bounds.min_x) *
                (double)(width - 1)
                );

        py =
            (int)
            (
                (bounds.max_y - y) /
                (bounds.max_y - bounds.min_y) *
                (double)(height - 1)
                );

        image_add_pixel(
            image,
            px,
            py,
            trail
        );
    }

    if (
        trajectory->count > skip
        )
    {
        const State* last =
            &trajectory->data[
                trajectory->count - 1
            ];

        int px =
            (int)
            (
                (last->v[x_index] -
                    bounds.min_x) /
                (bounds.max_x -
                    bounds.min_x) *
                (double)(width - 1)
                );

        int py =
            (int)
            (
                (bounds.max_y -
                    last->v[y_index]) /
                (bounds.max_y -
                    bounds.min_y) *
                (double)(height - 1)
                );

        image_set_pixel(
            image,
            px,
            py,
            head
        );
    }

    if (
        image_write_ppm(
            image,
            filename
        )
        )
    {
        printf(
            "PPM written: %s\n",
            filename
        );
    }
    else
    {
        printf(
            "Failed to write PPM.\n"
        );
    }

    image_destroy(image);
}


/* ================================================================
 * CSV export
 * ================================================================ */

static int trajectory_write_csv(
    const Trajectory* trajectory,
    const char* filename
)
{
    FILE* file;

    size_t i;

    int j;

    if (trajectory->count == 0)
        return 0;

    file =
        fopen(
            filename,
            "w"
        );

    if (!file)
        return 0;

    fprintf(
        file,
        "index"
    );

    for (
        j = 0;
        j < trajectory->data[0].n;
        ++j
        )
    {
        fprintf(
            file,
            ",x%d",
            j
        );
    }

    fprintf(file, "\n");

    for (
        i = 0;
        i < trajectory->count;
        ++i
        )
    {
        const State* state =
            &trajectory->data[i];

        fprintf(
            file,
            "%zu",
            i
        );

        for (
            j = 0;
            j < state->n;
            ++j
            )
        {
            fprintf(
                file,
                ",%.17g",
                state->v[j]
            );
        }

        fprintf(file, "\n");
    }

    fclose(file);

    return 1;
}


/* ================================================================
 * Logistic bifurcation diagram
 * ================================================================ */

static void generate_logistic_bifurcation(
    const char* filename,
    int width,
    int height,
    double r_min,
    double r_max,
    int transient,
    int samples
)
{
    Image* image;

    Pixel background =
    { 2, 2, 5 };

    Pixel point =
    { 245, 245, 245 };

    int x;

    image =
        image_create(
            width,
            height
        );

    image_clear(
        image,
        background
    );

    for (
        x = 0;
        x < width;
        ++x
        )
    {
        double r =
            r_min +
            (r_max - r_min) *
            (double)x /
            (double)(width - 1);

        double value = 0.5;

        int i;

        for (
            i = 0;
            i < transient;
            ++i
            )
        {
            value =
                r *
                value *
                (1.0 - value);
        }

        for (
            i = 0;
            i < samples;
            ++i
            )
        {
            int y;

            value =
                r *
                value *
                (1.0 - value);

            y =
                (int)
                (
                    (1.0 - value) *
                    (double)(height - 1)
                    );

            image_add_pixel(
                image,
                x,
                y,
                point
            );
        }
    }

    if (
        image_write_ppm(
            image,
            filename
        )
        )
    {
        printf(
            "Bifurcation diagram written: %s\n",
            filename
        );
    }
    else
    {
        printf(
            "Failed to write bifurcation diagram.\n"
        );
    }

    image_destroy(image);
}


/* ================================================================
 * Lyapunov exponent
 *
 * This is a practical two-trajectory estimate:
 *
 *   lambda ~= average(
 *       ln(distance_new / distance_initial)
 *   ) / dt
 *
 * followed by renormalization.
 * ================================================================ */

static double lyapunov_continuous(
    const DynamicalSystem* system,
    const State* initial,
    double dt,
    int steps,
    int method,
    int transient,
    double epsilon
)
{
    State a;
    State b;

    State next_a;
    State next_b;

    double sum = 0.0;

    int count = 0;

    int i;

    state_copy(&a, initial);
    state_copy(&b, initial);

    b.v[0] += epsilon;

    for (
        i = 0;
        i < steps;
        ++i
        )
    {
        double time =
            (double)i * dt;

        double distance;

        double scale;

        if (method == 0)
        {
            euler_step(
                system->derivative,
                time,
                dt,
                &a,
                &next_a,
                system->parameters
            );

            euler_step(
                system->derivative,
                time,
                dt,
                &b,
                &next_b,
                system->parameters
            );
        }
        else
        {
            rk4_step(
                system->derivative,
                time,
                dt,
                &a,
                &next_a,
                system->parameters
            );

            rk4_step(
                system->derivative,
                time,
                dt,
                &b,
                &next_b,
                system->parameters
            );
        }

        state_copy(
            &a,
            &next_a
        );

        state_copy(
            &b,
            &next_b
        );

        if (i < transient)
            continue;

        distance =
            state_distance(
                &a,
                &b
            );

        if (
            !isfinite(distance) ||
            distance <= 0.0
            )
        {
            continue;
        }

        sum +=
            log(
                distance /
                epsilon
            );

        ++count;

        scale =
            epsilon /
            distance;

        for (
            int j = 0;
            j < b.n;
            ++j
            )
        {
            b.v[j] =
                a.v[j] +
                (
                    b.v[j] -
                    a.v[j]
                    ) *
                scale;
        }
    }

    if (count == 0)
        return NAN;

    return
        sum /
        (
            (double)count *
            dt
            );
}


static double lyapunov_map(
    const DynamicalSystem* system,
    const State* initial,
    int steps,
    int transient,
    double epsilon
)
{
    State a;
    State b;

    State next_a;
    State next_b;

    double sum = 0.0;

    int count = 0;

    int i;

    state_copy(&a, initial);
    state_copy(&b, initial);

    b.v[0] += epsilon;

    for (
        i = 0;
        i < steps;
        ++i
        )
    {
        double distance;
        double scale;

        system->map(
            &a,
            &next_a,
            system->parameters
        );

        system->map(
            &b,
            &next_b,
            system->parameters
        );

        state_copy(
            &a,
            &next_a
        );

        state_copy(
            &b,
            &next_b
        );

        if (i < transient)
            continue;

        distance =
            state_distance(
                &a,
                &b
            );

        if (
            !isfinite(distance) ||
            distance <= 0.0
            )
        {
            continue;
        }

        sum +=
            log(
                distance /
                epsilon
            );

        ++count;

        scale =
            epsilon /
            distance;

        for (
            int j = 0;
            j < b.n;
            ++j
            )
        {
            b.v[j] =
                a.v[j] +
                (
                    b.v[j] -
                    a.v[j]
                    ) *
                scale;
        }
    }

    if (count == 0)
        return NAN;

    return
        sum /
        (double)count;
}


/* ================================================================
 * Poincaré section
 * ================================================================ */

static void poincare_export(
    const Trajectory* trajectory,
    int coordinate,
    double crossing,
    const char* filename
)
{
    FILE* file;

    size_t i;

    int hits = 0;

    if (trajectory->count < 2)
    {
        printf(
            "Not enough trajectory points.\n"
        );

        return;
    }

    if (trajectory->data[0].n < 3)
    {
        printf(
            "Poincaré section requires >= 3 dimensions.\n"
        );

        return;
    }

    file =
        fopen(
            filename,
            "w"
        );

    if (!file)
    {
        printf(
            "Cannot open %s\n",
            filename
        );

        return;
    }

    fprintf(
        file,
        "index,x,y\n"
    );

    for (
        i = 1;
        i < trajectory->count;
        ++i
        )
    {
        double previous =
            trajectory->data[i - 1]
            .v[coordinate];

        double current =
            trajectory->data[i]
            .v[coordinate];

        bool crossing_detected =
            (
                previous < crossing &&
                current >= crossing
                )
            ||
            (
                previous > crossing &&
                current <= crossing
                );

        if (crossing_detected)
        {
            double x =
                trajectory->data[i].v[0];

            double y =
                trajectory->data[i].v[1];

            fprintf(
                file,
                "%d,%.17g,%.17g\n",
                hits,
                x,
                y
            );

            ++hits;
        }
    }

    fclose(file);

    printf(
        "Poincaré section: %d crossings -> %s\n",
        hits,
        filename
    );
}


/* ================================================================
 * Statistics
 * ================================================================ */

static void trajectory_statistics(
    const Trajectory* trajectory,
    int index
)
{
    size_t i;

    size_t count = 0;

    double sum = 0.0;
    double sum2 = 0.0;

    double minimum = DBL_MAX;
    double maximum = -DBL_MAX;

    for (
        i = 0;
        i < trajectory->count;
        ++i
        )
    {
        double value =
            trajectory->data[i].v[index];

        if (!isfinite(value))
            continue;

        sum += value;
        sum2 += value * value;

        if (value < minimum)
            minimum = value;

        if (value > maximum)
            maximum = value;

        ++count;
    }

    if (count == 0)
    {
        printf(
            "No finite samples.\n"
        );

        return;
    }

    {
        double mean =
            sum / (double)count;

        double variance =
            sum2 / (double)count -
            mean * mean;

        if (variance < 0.0)
            variance = 0.0;

        printf("\n");
        printf(
            "Statistics for x%d\n",
            index
        );

        printf(
            "------------------------------\n"
        );

        printf(
            "Samples : %zu\n",
            count
        );

        printf(
            "Minimum : %.12g\n",
            minimum
        );

        printf(
            "Maximum : %.12g\n",
            maximum
        );

        printf(
            "Mean    : %.12g\n",
            mean
        );

        printf(
            "Std Dev : %.12g\n",
            sqrt(variance)
        );
    }
}


/* ================================================================
 * Configure system
 * ================================================================ */

static void configure_system(
    int system_id,
    DynamicalSystem* system,
    State* initial
)
{
    static LogisticParameters logistic;

    static LorenzParameters lorenz;

    static RosslerParameters rossler;

    static HenonParameters henon;

    static IkedaParameters ikeda;

    static DuffingParameters duffing;

    static PendulumParameters pendulum;

    state_zero(
        initial,
        1
    );

    switch (system_id)
    {
    case 1:
    {
        logistic.r =
            ask_double(
                "Logistic r",
                0.0,
                4.0,
                3.9
            );

        initial->n = 1;

        initial->v[0] =
            ask_double(
                "Initial x",
                1e-12,
                1.0 - 1e-12,
                0.5
            );

        *system =
            make_logistic(
                &logistic
            );

        break;
    }

    case 2:
    {
        lorenz.sigma =
            ask_double(
                "Sigma",
                0.0,
                100.0,
                10.0
            );

        lorenz.rho =
            ask_double(
                "Rho",
                0.0,
                100.0,
                28.0
            );

        lorenz.beta =
            ask_double(
                "Beta",
                0.0,
                100.0,
                8.0 / 3.0
            );

        initial->n = 3;

        initial->v[0] =
            ask_double(
                "Initial X",
                -1000.0,
                1000.0,
                0.1
            );

        initial->v[1] =
            ask_double(
                "Initial Y",
                -1000.0,
                1000.0,
                0.0
            );

        initial->v[2] =
            ask_double(
                "Initial Z",
                -1000.0,
                1000.0,
                0.0
            );

        *system =
            make_lorenz(
                &lorenz
            );

        break;
    }

    case 3:
    {
        rossler.a =
            ask_double(
                "a",
                -10.0,
                10.0,
                0.2
            );

        rossler.b =
            ask_double(
                "b",
                -10.0,
                10.0,
                0.2
            );

        rossler.c =
            ask_double(
                "c",
                -10.0,
                30.0,
                5.7
            );

        initial->n = 3;

        initial->v[0] =
            ask_double(
                "Initial X",
                -1000.0,
                1000.0,
                0.1
            );

        initial->v[1] =
            ask_double(
                "Initial Y",
                -1000.0,
                1000.0,
                0.0
            );

        initial->v[2] =
            ask_double(
                "Initial Z",
                -1000.0,
                1000.0,
                0.0
            );

        *system =
            make_rossler(
                &rossler
            );

        break;
    }

    case 4:
    {
        henon.a =
            ask_double(
                "a",
                0.0,
                2.0,
                1.4
            );

        henon.b =
            ask_double(
                "b",
                -1.0,
                1.0,
                0.3
            );

        initial->n = 2;

        initial->v[0] =
            ask_double(
                "Initial x",
                -10.0,
                10.0,
                0.1
            );

        initial->v[1] =
            ask_double(
                "Initial y",
                -10.0,
                10.0,
                0.1
            );

        *system =
            make_henon(
                &henon
            );

        break;
    }

    case 5:
    {
        ikeda.u =
            ask_double(
                "u",
                0.0,
                2.0,
                0.9
            );

        initial->n = 2;

        initial->v[0] =
            ask_double(
                "Initial x",
                -10.0,
                10.0,
                0.1
            );

        initial->v[1] =
            ask_double(
                "Initial y",
                -10.0,
                10.0,
                0.1
            );

        *system =
            make_ikeda(
                &ikeda
            );

        break;
    }

    case 6:
    {
        duffing.delta =
            ask_double(
                "delta",
                0.0,
                10.0,
                0.2
            );

        duffing.alpha =
            ask_double(
                "alpha",
                -10.0,
                10.0,
                -1.0
            );

        duffing.beta =
            ask_double(
                "beta",
                -10.0,
                10.0,
                1.0
            );

        duffing.gamma =
            ask_double(
                "gamma",
                0.0,
                10.0,
                0.3
            );

        duffing.omega =
            ask_double(
                "omega",
                0.001,
                20.0,
                1.2
            );

        initial->n = 2;

        initial->v[0] =
            ask_double(
                "Initial x",
                -100.0,
                100.0,
                0.1
            );

        initial->v[1] =
            ask_double(
                "Initial velocity",
                -100.0,
                100.0,
                0.0
            );

        *system =
            make_duffing(
                &duffing
            );

        break;
    }

    case 7:
    {
        pendulum.m1 =
            ask_double(
                "Mass 1",
                0.001,
                100.0,
                1.0
            );

        pendulum.m2 =
            ask_double(
                "Mass 2",
                0.001,
                100.0,
                1.0
            );

        pendulum.l1 =
            ask_double(
                "Length 1",
                0.001,
                100.0,
                1.0
            );

        pendulum.l2 =
            ask_double(
                "Length 2",
                0.001,
                100.0,
                1.0
            );

        pendulum.g =
            ask_double(
                "Gravity",
                0.0,
                100.0,
                9.81
            );

        initial->n = 4;

        initial->v[0] =
            ask_double(
                "Theta 1 (radians)",
                -10.0,
                10.0,
                M_PI * 0.9
            );

        initial->v[1] =
            ask_double(
                "Omega 1",
                -100.0,
                100.0,
                0.0
            );

        initial->v[2] =
            ask_double(
                "Theta 2 (radians)",
                -10.0,
                10.0,
                M_PI * 0.7
            );

        initial->v[3] =
            ask_double(
                "Omega 2",
                -100.0,
                100.0,
                0.0
            );

        *system =
            make_pendulum(
                &pendulum
            );

        break;
    }

    default:
        fatal_error(
            "Unknown system."
        );
    }
}


/* ================================================================
 * Run simulation
 * ================================================================ */

static void run_simulation(
    int system_id
)
{
    DynamicalSystem system;

    State initial;

    SimulationConfig config;

    Trajectory* trajectory;

    printf("\n");
    printf("====================================================\n");
    printf(" SYSTEM CONFIGURATION\n");
    printf("====================================================\n");

    configure_system(
        system_id,
        &system,
        &initial
    );

    printf("\nSystem: %s\n", system.name);
    printf("Initial state: ");
    print_state(&initial);
    printf("\n");

    config.t0 = 0.0;

    if (system.map)
    {
        config.dt = 1.0;

        config.steps =
            ask_int(
                "Iterations",
                10,
                1000000,
                10000
            );
    }
    else
    {
        config.dt =
            ask_double(
                "Time step dt",
                1e-6,
                10.0,
                0.01
            );

        config.steps =
            ask_int(
                "Integration steps",
                10,
                1000000,
                10000
            );
    }

    int method = 1;

    if (!system.map)
    {
        method =
            ask_int(
                "Numerical method (0=Euler, 1=RK4)",
                0,
                1,
                1
            );
    }

    trajectory =
        trajectory_create(
            INITIAL_CAPACITY
        );

    printf(
        "\nRunning simulation...\n"
    );

    clock_t start =
        clock();

    if (system.map)
    {
        iterate_map(
            &system,
            &initial,
            config.steps,
            trajectory
        );
    }
    else
    {
        integrate_system(
            &system,
            &initial,
            &config,
            method,
            trajectory
        );
    }

    clock_t end =
        clock();

    double elapsed =
        (double)(end - start) /
        (double)CLOCKS_PER_SEC;

    printf(
        "Simulation finished in %.6f seconds.\n",
        elapsed
    );

    printf(
        "Generated %zu states.\n",
        trajectory->count
    );

    if (trajectory->count == 0)
    {
        trajectory_destroy(trajectory);
        return;
    }

    int transient_percent =
        ask_int(
            "Discard transient (%)",
            0,
            99,
            10
        );

    size_t skip =
        trajectory->count *
        (size_t)transient_percent /
        100;

    int x_index = 0;
    int y_index = 0;

    if (system.dimension >= 2)
    {
        x_index =
            ask_int(
                "X axis state index",
                0,
                system.dimension - 1,
                0
            );

        y_index =
            ask_int(
                "Y axis state index",
                0,
                system.dimension - 1,
                1
            );
    }

    ascii_plot(
        trajectory,
        x_index,
        y_index,
        DEFAULT_ASCII_WIDTH,
        DEFAULT_ASCII_HEIGHT,
        skip
    );

    printf("\n");
    printf("----------------------------------------------------\n");
    printf(" ANALYSIS\n");
    printf("----------------------------------------------------\n");
    printf(" 1. Export CSV\n");
    printf(" 2. Export PPM\n");
    printf(" 3. Statistics\n");
    printf(" 4. Poincaré Section\n");
    printf(" 5. Lyapunov Exponent\n");
    printf(" 6. All of the above\n");
    printf(" 0. Back\n");

    int option =
        ask_int(
            "Select",
            0,
            6,
            1
        );

    if (
        option == 1 ||
        option == 6
        )
    {
        if (
            trajectory_write_csv(
                trajectory,
                "trajectory.csv"
            )
            )
        {
            printf(
                "Wrote trajectory.csv\n"
            );
        }
        else
        {
            printf(
                "CSV export failed.\n"
            );
        }
    }

    if (
        option == 2 ||
        option == 6
        )
    {
        render_trajectory_ppm(
            trajectory,
            x_index,
            y_index,
            "trajectory.ppm",
            DEFAULT_IMAGE_WIDTH,
            DEFAULT_IMAGE_HEIGHT,
            skip
        );
    }

    if (
        option == 3 ||
        option == 6
        )
    {
        int index =
            ask_int(
                "Statistics state index",
                0,
                system.dimension - 1,
                0
            );

        trajectory_statistics(
            trajectory,
            index
        );
    }

    if (
        option == 4 ||
        option == 6
        )
    {
        if (system.dimension < 3)
        {
            printf(
                "Poincaré sections need dimension >= 3.\n"
            );
        }
        else
        {
            int coordinate =
                ask_int(
                    "Crossing coordinate",
                    0,
                    system.dimension - 1,
                    2
                );

            double crossing =
                ask_double(
                    "Crossing value",
                    -10000.0,
                    10000.0,
                    0.0
                );

            poincare_export(
                trajectory,
                coordinate,
                crossing,
                "poincare.csv"
            );
        }
    }

    if (
        option == 5 ||
        option == 6
        )
    {
        double epsilon =
            ask_double(
                "Perturbation epsilon",
                1e-15,
                1.0,
                EPSILON_DEFAULT
            );

        int steps =
            ask_int(
                "Lyapunov steps",
                100,
                1000000,
                50000
            );

        int transient =
            ask_int(
                "Lyapunov transient steps",
                0,
                steps - 1,
                steps / 10
            );

        double lambda;

        if (system.map)
        {
            lambda =
                lyapunov_map(
                    &system,
                    &initial,
                    steps,
                    transient,
                    epsilon
                );
        }
        else
        {
            lambda =
                lyapunov_continuous(
                    &system,
                    &initial,
                    config.dt,
                    steps,
                    method,
                    transient,
                    epsilon
                );
        }

        printf("\n");
        printf(
            "Largest Lyapunov exponent ≈ %.12g\n",
            lambda
        );

        if (isfinite(lambda))
        {
            if (lambda > 0.0)
            {
                printf(
                    "Classification: positive divergence / chaotic behavior.\n"
                );
            }
            else if (fabs(lambda) < 1e-4)
            {
                printf(
                    "Classification: approximately neutral.\n"
                );
            }
            else
            {
                printf(
                    "Classification: contraction / non-chaotic tendency.\n"
                );
            }
        }
    }

    trajectory_destroy(trajectory);
}


/* ================================================================
 * Sensitivity experiment
 * ================================================================ */

static void run_sensitivity(void)
{
    LorenzParameters parameters;

    DynamicalSystem system;

    State first;
    State second;

    double dt;

    int steps;

    double perturbation;

    FILE* file;

    printf("\n");
    printf("====================================================\n");
    printf(" INITIAL CONDITION SENSITIVITY\n");
    printf("====================================================\n");

    parameters.sigma = 10.0;
    parameters.rho = 28.0;
    parameters.beta = 8.0 / 3.0;

    parameters.sigma =
        ask_double(
            "Sigma",
            0.0,
            100.0,
            parameters.sigma
        );

    parameters.rho =
        ask_double(
            "Rho",
            0.0,
            100.0,
            parameters.rho
        );

    parameters.beta =
        ask_double(
            "Beta",
            0.0,
            100.0,
            parameters.beta
        );

    system =
        make_lorenz(
            &parameters
        );

    dt =
        ask_double(
            "dt",
            1e-6,
            1.0,
            0.01
        );

    steps =
        ask_int(
            "Steps",
            10,
            1000000,
            5000
        );

    perturbation =
        ask_double(
            "Initial perturbation",
            1e-15,
            1.0,
            1e-8
        );

    first.n = 3;

    first.v[0] = 0.1;
    first.v[1] = 0.0;
    first.v[2] = 0.0;

    state_copy(
        &second,
        &first
    );

    second.v[0] += perturbation;

    file =
        fopen(
            "sensitivity.csv",
            "w"
        );

    if (!file)
    {
        printf(
            "Could not create sensitivity.csv\n"
        );

        return;
    }

    fprintf(
        file,
        "step,time,distance\n"
    );

    printf("\n");

    for (int i = 0; i <= steps; ++i)
    {
        double distance =
            state_distance(
                &first,
                &second
            );

        fprintf(
            file,
            "%d,%.17g,%.17g\n",
            i,
            (double)i * dt,
            distance
        );

        if (
            i < 30 ||
            i % (steps / 20 + 1) == 0 ||
            i == steps
            )
        {
            printf(
                "step=%7d  t=%10.4f  distance=%14.8g\n",
                i,
                (double)i * dt,
                distance
            );
        }

        if (i == steps)
            break;

        State next_first;
        State next_second;

        rk4_step(
            system.derivative,
            (double)i * dt,
            dt,
            &first,
            &next_first,
            system.parameters
        );

        rk4_step(
            system.derivative,
            (double)i * dt,
            dt,
            &second,
            &next_second,
            system.parameters
        );

        state_copy(
            &first,
            &next_first
        );

        state_copy(
            &second,
            &next_second
        );
    }

    fclose(file);

    printf(
        "\nWrote sensitivity.csv\n"
    );
}


/* ================================================================
 * Benchmark
 * ================================================================ */

static void run_benchmark(void)
{
    LorenzParameters parameters;

    DynamicalSystem system;

    State initial;

    SimulationConfig config;

    Trajectory* trajectory;

    clock_t start;
    clock_t end;

    double elapsed;

    parameters.sigma = 10.0;
    parameters.rho = 28.0;
    parameters.beta = 8.0 / 3.0;

    system =
        make_lorenz(
            &parameters
        );

    initial.n = 3;

    initial.v[0] = 0.1;
    initial.v[1] = 0.0;
    initial.v[2] = 0.0;

    config.t0 = 0.0;
    config.dt = 0.01;
    config.steps = 200000;

    trajectory =
        trajectory_create(
            INITIAL_CAPACITY
        );

    printf("\n");
    printf("====================================================\n");
    printf(" BENCHMARK\n");
    printf("====================================================\n");

    printf(
        "System     : Lorenz\n"
    );

    printf(
        "Integrator : RK4\n"
    );

    printf(
        "Steps      : %d\n",
        config.steps
    );

    printf(
        "dt         : %g\n",
        config.dt
    );

    start = clock();

    integrate_system(
        &system,
        &initial,
        &config,
        1,
        trajectory
    );

    end = clock();

    elapsed =
        (double)(end - start) /
        (double)CLOCKS_PER_SEC;

    printf(
        "\nElapsed CPU time: %.6f sec\n",
        elapsed
    );

    if (elapsed > 0.0)
    {
        printf(
            "Steps / second : %.2f\n",
            (double)config.steps /
            elapsed
        );
    }

    printf(
        "Generated states: %zu\n",
        trajectory->count
    );

    trajectory_destroy(
        trajectory
    );
}


/* ================================================================
 * Quick Lorenz demo
 * ================================================================ */

static void quick_demo(void)
{
    LorenzParameters parameters;

    DynamicalSystem system;

    State initial;

    SimulationConfig config;

    Trajectory* trajectory;

    parameters.sigma = 10.0;
    parameters.rho = 28.0;
    parameters.beta = 8.0 / 3.0;

    system =
        make_lorenz(
            &parameters
        );

    initial.n = 3;

    initial.v[0] = 0.1;
    initial.v[1] = 0.0;
    initial.v[2] = 0.0;

    config.t0 = 0.0;
    config.dt = 0.01;
    config.steps = 10000;

    trajectory =
        trajectory_create(
            INITIAL_CAPACITY
        );

    printf(
        "\nRunning Lorenz attractor...\n"
    );

    integrate_system(
        &system,
        &initial,
        &config,
        1,
        trajectory
    );

    ascii_plot(
        trajectory,
        0,
        2,
        DEFAULT_ASCII_WIDTH,
        DEFAULT_ASCII_HEIGHT,
        1000
    );

    printf(
        "\nExporting quick-demo PPM...\n"
    );

    render_trajectory_ppm(
        trajectory,
        0,
        2,
        "lorenz.ppm",
        1200,
        900,
        1000
    );

    printf(
        "Quick demo complete.\n"
    );

    trajectory_destroy(
        trajectory
    );
}


/* ================================================================
 * Help
 * ================================================================ */

static void print_help(void)
{
    printf("\n");
    printf("====================================================\n");
    printf(" CHAOS LABORATORY HELP\n");
    printf("====================================================\n");

    printf(
        "\nThis program numerically explores nonlinear\n"
        "dynamical systems and chaotic behavior.\n"
    );

    printf(
        "\nContinuous systems:\n"
        "  Lorenz\n"
        "  Rössler\n"
        "  Duffing\n"
        "  Double Pendulum\n"
    );

    printf(
        "\nDiscrete systems:\n"
        "  Logistic Map\n"
        "  Hénon Map\n"
        "  Ikeda Map\n"
    );

    printf(
        "\nNumerical methods:\n"
        "  Euler\n"
        "  RK4\n"
    );

    printf(
        "\nOutput files:\n"
        "  trajectory.csv\n"
        "  trajectory.ppm\n"
        "  poincare.csv\n"
        "  sensitivity.csv\n"
        "  bifurcation.ppm\n"
        "  lorenz.ppm\n"
    );

    printf(
        "\nImportant:\n"
        "A positive Lyapunov exponent is a strong numerical\n"
        "indicator of sensitive chaotic dynamics, but the\n"
        "estimate depends on timestep, transient removal,\n"
        "perturbation size, numerical precision, and the\n"
        "specific algorithm used.\n"
    );

    printf(
        "\nPPM is intentionally used because this program has\n"
        "no dependency on graphical libraries.\n"
    );
}


/* ================================================================
 * Menu
 * ================================================================ */

static void print_menu(void)
{
    printf("\n");

    printf(
        "====================================================\n"
    );

    printf(
        "                 CHAOS LABORATORY\n"
    );

    printf(
        "                 PURE C99 / %s\n",
        VERSION
    );

    printf(
        "====================================================\n"
    );

    printf("\n");

    printf(
        " DYNAMICAL SYSTEMS\n"
    );

    printf(
        "  [1] Logistic Map\n"
    );

    printf(
        "  [2] Lorenz Attractor\n"
    );

    printf(
        "  [3] Rössler Attractor\n"
    );

    printf(
        "  [4] Hénon Map\n"
    );

    printf(
        "  [5] Ikeda Map\n"
    );

    printf(
        "  [6] Duffing Oscillator\n"
    );

    printf(
        "  [7] Double Pendulum\n"
    );

    printf("\n");

    printf(
        " CHAOS ANALYSIS\n"
    );

    printf(
        "  [8] Logistic Bifurcation Diagram\n"
    );

    printf(
        "  [9] Initial Condition Sensitivity\n"
    );

    printf(
        " [10] Quick Lorenz Demo\n"
    );

    printf("\n");

    printf(
        " TOOLS\n"
    );

    printf(
        " [11] Benchmark\n"
    );

    printf(
        " [12] Help\n"
    );

    printf(
        "  [0] Exit\n"
    );

    printf("\n");
}


/* ================================================================
 * Main
 * ================================================================ */

int main(void)
{
    int choice;

    printf("\n");

    printf(
        "****************************************************\n"
    );

    printf(
        "*                                                  *\n"
    );

    printf(
        "*              CHAOS LABORATORY                   *\n"
    );

    printf(
        "*                 PURE C99                        *\n"
    );

    printf(
        "*                                                  *\n"
    );

    printf(
        "****************************************************\n"
    );

    printf(
        "\n"
        "No external libraries.\n"
        "No C++.\n"
        "No GUI toolkit.\n"
        "Just C, mathematics, memory, and questionable decisions.\n"
    );

    for (;;)
    {
        print_menu();

        choice =
            ask_int(
                "Select an experiment",
                0,
                12,
                10
            );

        switch (choice)
        {
        case 0:
        {
            printf(
                "\nThe butterfly has left the laboratory.\n"
            );

            return 0;
        }

        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
        case 6:
        case 7:
        {
            run_simulation(
                choice
            );

            pause_screen();

            break;
        }

        case 8:
        {
            char filename[256];

            double minimum_r;

            double maximum_r;

            int width;

            int height;

            int transient;

            int samples;

            printf("\n");
            printf(
                "====================================================\n"
            );

            printf(
                " LOGISTIC MAP BIFURCATION DIAGRAM\n"
            );

            printf(
                "====================================================\n"
            );

            minimum_r =
                ask_double(
                    "Minimum r",
                    0.0,
                    4.0,
                    2.5
                );

            maximum_r =
                ask_double(
                    "Maximum r",
                    minimum_r + 0.0001,
                    4.0,
                    4.0
                );

            width =
                ask_int(
                    "Image width",
                    100,
                    5000,
                    1600
                );

            height =
                ask_int(
                    "Image height",
                    100,
                    3000,
                    900
                );

            transient =
                ask_int(
                    "Transient iterations",
                    10,
                    1000000,
                    1000
                );

            samples =
                ask_int(
                    "Plotted iterations",
                    10,
                    10000,
                    300
                );

            printf(
                "Filename [bifurcation.ppm]: "
            );

            read_line(
                filename,
                sizeof(filename)
            );

            if (filename[0] == '\0')
                strcpy(
                    filename,
                    "bifurcation.ppm"
                );

            printf(
                "\nGenerating bifurcation diagram...\n"
            );

            generate_logistic_bifurcation(
                filename,
                width,
                height,
                minimum_r,
                maximum_r,
                transient,
                samples
            );

            pause_screen();

            break;
        }

        case 9:
        {
            run_sensitivity();

            pause_screen();

            break;
        }

        case 10:
        {
            quick_demo();

            pause_screen();

            break;
        }

        case 11:
        {
            run_benchmark();

            pause_screen();

            break;
        }

        case 12:
        {
            print_help();

            pause_screen();

            break;
        }

        default:
            break;
        }
    }

    return 0;
}
