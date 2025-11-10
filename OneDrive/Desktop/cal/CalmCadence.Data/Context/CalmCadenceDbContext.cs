using System;
using Microsoft.EntityFrameworkCore;
using CalmCadence.Core.Models;

namespace CalmCadence.Data.Context;

public class CalmCadenceDbContext : DbContext
{
    public DbSet<Project> Projects => Set<Project>();
    public DbSet<TaskItem> Tasks => Set<TaskItem>();
    public DbSet<EventItem> Events => Set<EventItem>();
    public DbSet<Habit> Habits => Set<Habit>();
    public DbSet<HabitLog> HabitLogs => Set<HabitLog>();
    public DbSet<Routine> Routines => Set<Routine>();
    public DbSet<Settings> Settings => Set<Settings>();
    public DbSet<DailyMedia> DailyMedia => Set<DailyMedia>();
    public DbSet<BriefCache> BriefCache => Set<BriefCache>();

    public CalmCadenceDbContext(DbContextOptions<CalmCadenceDbContext> options)
        : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(CalmCadenceDbContext).Assembly);

        // Singleton Settings row
        modelBuilder.Entity<Settings>()
            .HasKey(s => s.Id);
        modelBuilder.Entity<Settings>()
            .HasData(new Settings { Id = 1 });
    }
}
